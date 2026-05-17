import sys
import os
import asyncio
import logging

try:
    from reflex_loop import config
except ImportError:
    import config

from reflex_loop.session import SessionContext
from reflex_loop.turn_manager import TurnManager
from reflex_loop.audio.mic_stream import MicrophoneStream
from reflex_loop.audio.player import AudioPlayer
from reflex_loop.asr.transcriber import DeepgramStreamer
from reflex_loop.llm.streaming_client import LLMClient, ConversationMemory
from reflex_loop.tts.tts_client import TTSClient
from reflex_loop.memory import MemoryManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("main")

# Load system prompt
try:
    with open(os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.txt"), "r") as f:
        SYSTEM_PROMPT_TEXT = f.read().strip()
except FileNotFoundError:
    SYSTEM_PROMPT_TEXT = getattr(config, "SYSTEM_PROMPT", "You are a helpful assistant.")

class ReflexAgent:
    def __init__(self, loop):
        logger.info("Initializing eFLEX LOOP Voice Agent...")
        
        self.loop = loop
        self.session = SessionContext()
        self.turn_manager = TurnManager()
        
        # Queues
        self.transcript_queue = asyncio.Queue()  # ASR -> LLM
        self.text_chunk_queue = asyncio.Queue()  # LLM -> TTS
        
        # Components
        self.mic = MicrophoneStream(self.loop)
        self.player = AudioPlayer()
        self.asr = DeepgramStreamer(self.transcript_queue, self.loop)
        self.llm = LLMClient()
        self.tts = TTSClient()
        try:
            self.memory_manager = MemoryManager()
        except Exception as e:
            logger.error(f"Failed to initialize MemoryManager: {e}")
            self.memory_manager = None
        
        self.running = True
        self.memory = ConversationMemory(SYSTEM_PROMPT_TEXT, max_turns=10)
        self.llm_task = None
        
    async def run(self):
        logger.info("\n--- AGENT RUNNING. Speak now. (Ctrl+C to stop) ---\n")
        
        self.asr.start()
        
        # Start core loops
        bg_tasks = [
            asyncio.create_task(self._audio_ingestion_loop()),
            asyncio.create_task(self._thought_generator_loop()),
            asyncio.create_task(self._tts_worker_loop())
        ]
        
        try:
            await asyncio.gather(*bg_tasks)
        except asyncio.CancelledError:
            pass
        finally:
            self.running = False
            self.asr.stop()
            self.player.terminate()

    async def _audio_ingestion_loop(self):
        """Pushes microphone frames to the ASR."""
        try:
            with self.mic as stream:
                async for audio_frame in stream.async_generator():
                    if not self.running:
                        break
                    
                    # We no longer use local VAD blocking interrupts. 
                    # All audio goes directly to ASR, and Deepgram interim results trigger the TurnManager.
                    self.asr.process_audio(audio_frame)
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Mic error: {e}")

    async def _thought_generator_loop(self):
        """
        Listens to ASR transcripts, evaluates interrupts with TurnManager, and spawns LLM tasks.
        """
        while self.running:
            payload = await self.transcript_queue.get()
            event_type = payload.get("type", "Transcript")
            text = payload.get("text", "")
            is_final = payload.get("is_final", False)
            
            # --- THE DUPLEX BARGE-IN LOGIC ---
            if self.session.is_speaking and not self.session.is_interrupted:
                # Interrupt instantly on SpeechStarted or if it's a true interim text interruption
                if event_type == "SpeechStarted" or self.turn_manager.is_true_interruption(text):
                    logger.warning(f"[{self.session.session_id}] SEMANTIC INTERRUPT (Trigger: {event_type}) '{text}'")
                    
                    self.player.stop()
                    await self.session.trigger_interrupt()
                    
                    if self.llm_task and not self.llm_task.done():
                         self.llm_task.cancel()
                         try:
                             await self.llm_task
                         except asyncio.CancelledError:
                             pass
                    
                    while not self.text_chunk_queue.empty():
                        try:
                            self.text_chunk_queue.get_nowait()
                            self.text_chunk_queue.task_done()
                        except asyncio.QueueEmpty:
                            break
                elif event_type == "Transcript" and not self.turn_manager.is_true_interruption(text):
                    # It was just a backchannel like "mhm". Ignore it.
                    self.transcript_queue.task_done()
                    continue

            # --- NORMAL PROCESSING ---
            if (is_final and text) or (event_type == "UtteranceEnd" and text):
                logger.info(f"User (Final): {text}")
                self.memory.append("user", text)
                
                # Clear interrupt before we generate the new response
                if self.session.is_interrupted:
                    await self.session.clear_interrupt()
                    
                # Fire the LLM
                self.llm_task = asyncio.create_task(self._generate_response())
                
            self.transcript_queue.task_done()

    async def _generate_response(self):
        """Spins up the LLM stream. Can be killed at any time by the interrupt flag."""
        chunk_buffer = ""
        full_response = ""
        
        try:
            async for token in self.llm.stream_chat(self.memory, self.session, memory_manager=self.memory_manager):
                if self.session.is_interrupted:
                    logger.info("LLM Generation aborted mid-sentence.")
                    if full_response:
                        self.memory.append("model", full_response, interrupted=True)
                    return
                    
                full_response += token
                chunk_buffer += token
                
                word_count = len(chunk_buffer.split())
                is_first_chunk = len(full_response.split()) <= 3
                
                if (any(p in token for p in getattr(config, "PUNCTUATION_STOP", {'.', '?', '!'})) or 
                   (is_first_chunk and word_count >= 2) or 
                   word_count >= getattr(config, "TTS_FLUSH_WORDS", 5)):
                    await self.text_chunk_queue.put(chunk_buffer)
                    chunk_buffer = ""
                    
            if chunk_buffer and not self.session.is_interrupted:
                await self.text_chunk_queue.put(chunk_buffer)
                
            if full_response:
                self.memory.append("model", full_response)

        except asyncio.CancelledError:
            logger.info("LLM Generation cancelled via task cancellation.")
            if full_response:
                self.memory.append("model", full_response, interrupted=True)

    async def _tts_worker_loop(self):
        """
        Loop 4: The Voice.
        Reads text chunks, yields them into the TTS client generator, and plays the audio via player.
        """
        async def text_iterator():
            while self.running:
                try:
                    # Timeout resilient: Wait for chunks, but wake up periodically to check self.running
                    text_chunk = await asyncio.wait_for(self.text_chunk_queue.get(), timeout=1.0)
                    
                    if self.session.is_interrupted:
                        self.text_chunk_queue.task_done()
                        continue 

                    yield text_chunk
                    self.text_chunk_queue.task_done()
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break
                
        try:
            audio_stream = self.tts.stream_audio(text_iterator(), self.session)
            await self.player.play_stream(audio_stream, self.session)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"TTS Worker Error: {e}")

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    agent = ReflexAgent(loop)
    try:
        loop.run_until_complete(agent.run())
    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
        # Cancel all running tasks
        for task in asyncio.all_tasks(loop):
            task.cancel()
        loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(loop), return_exceptions=True))
    finally:
        loop.close()

if __name__ == "__main__":
    main()

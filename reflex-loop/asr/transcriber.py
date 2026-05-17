import os
import asyncio
import logging
from deepgram import (
    DeepgramClient,
    LiveTranscriptionEvents,
    LiveOptions,
)

logger = logging.getLogger(__name__)

# Try importing config, handle missing
try:
    from reflex_loop import config
except ImportError:
    import config

class DeepgramStreamer:
    def __init__(self, transcript_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self.transcript_queue = transcript_queue
        self.loop = loop
        
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key and config:
            api_key = getattr(config, "DEEPGRAM_API_KEY", None)
            
        if not api_key:
            raise ValueError("DEEPGRAM_API_KEY not found in environment")
            
        # Using the standard client because deepgram-sdk might not have AsyncDeepgramClient cleanly exposed in older versions,
        # but the callbacks run on another thread. We'll use loop.call_soon_threadsafe if needed, or if it supports async handlers, we use them.
        self.client = DeepgramClient(api_key)
        self.connection = self.client.listen.live.v("1")
        self.is_running = False

        # Register Event Handlers
        self.connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
        self.connection.on(LiveTranscriptionEvents.Error, self._on_error)
        self.connection.on(LiveTranscriptionEvents.Close, self._on_close)
        
        # New Barge-in and Utterance Events
        self.connection.on(LiveTranscriptionEvents.SpeechStarted, self._on_speech_started)
        self.connection.on(LiveTranscriptionEvents.UtteranceEnd, self._on_utterance_end)

    def start(self):
        if self.is_running:
            return

        logger.info("[ASR] Deepgram: Connecting...")
        options = LiveOptions(
            model="nova-2", 
            language="en-US", 
            smart_format=True, 
            interim_results=True, 
            endpointing=400,      # 400ms is more natural, avoids mid-sentence cutoffs
            vad_events=True,      # Let Deepgram's VAD help us
            utterance_end_ms=1000, # Safety net for slow speakers
            encoding="linear16", 
            channels=1, 
            sample_rate=16000
        )

        if self.connection.start(options) is False:
            logger.error("[ASR] Deepgram: Failed to start connection")
            return

        self.is_running = True
        logger.info("[ASR] Deepgram: Connected and listening.")

    def process_audio(self, audio_chunk):
        if self.is_running:
            self.connection.send(audio_chunk)

    def stop(self):
        self.is_running = False
        self.connection.finish()
        logger.info("[ASR] Deepgram: Stopped.")

    def _on_message(self, connection, result, **kwargs):
        """
        Runs in Deepgram SDK's background thread. We must push to the asyncio queue safely.
        """
        try:
            if result.channel and result.channel.alternatives:
                sentence = result.channel.alternatives[0].transcript
                
                if len(sentence) == 0:
                    return

                is_final = result.is_final
                
                payload = {
                    "type": "Transcript",
                    "text": sentence,
                    "is_final": is_final
                }
                
                # Push to asyncio queue safely from background thread
                asyncio.run_coroutine_threadsafe(self.transcript_queue.put(payload), self.loop)
                
        except Exception as e:
            logger.error(f"[ASR] Error processing message: {e}")

    def _on_speech_started(self, connection, speech_started, **kwargs):
        """Fires when Deepgram's VAD detects speech (approx 80-100ms latency)."""
        logger.debug("[ASR] SpeechStarted event received")
        payload = {
            "type": "SpeechStarted",
            "text": "",
            "is_final": False
        }
        asyncio.run_coroutine_threadsafe(self.transcript_queue.put(payload), self.loop)

    def _on_utterance_end(self, connection, utterance_end, **kwargs):
        """Fires when a long pause occurs, acting as a finalization safety net."""
        logger.debug("[ASR] UtteranceEnd event received")
        payload = {
            "type": "UtteranceEnd",
            "text": "",
            "is_final": True
        }
        asyncio.run_coroutine_threadsafe(self.transcript_queue.put(payload), self.loop)

    def _on_error(self, connection, error, **kwargs):
        logger.error(f"[ASR] Deepgram Error: {error}")

    def _on_close(self, connection, close, **kwargs):
        logger.info(f"[ASR] Connection Closed.")

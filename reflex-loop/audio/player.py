# audio/player.py
import pyaudio
import asyncio
import logging

try:
    from reflex_loop import config
except ImportError:
    import config

logger = logging.getLogger(__name__)

class AudioPlayer:
    def __init__(self):
        self._audio_interface = pyaudio.PyAudio()
        self.stream = None
        
        try:
            self.stream = self._audio_interface.open(
                format=pyaudio.paInt16,
                channels=getattr(config, "CHANNELS", 1),
                rate=getattr(config, "SAMPLE_RATE", 16000),
                output=True,
                frames_per_buffer=getattr(config, "CHUNK_SIZE", 480)
            )
        except Exception as e:
            logger.error(f"Error initializing audio output: {e}")
            self.stream = None

    def _sync_write(self, audio_chunk):
        if self.stream:
            try:
                self.stream.write(audio_chunk)
            except Exception as e:
                logger.error(f"Error playing chunk: {e}")

    async def play_stream(self, audio_generator, session):
        """
        Consumes an async generator of audio chunks.
        Stops immediately if session.is_interrupted is True.
        """
        if not self.stream:
            logger.error("Audio stream not initialized.")
            return

        await session.set_speaking(True)
        loop = asyncio.get_running_loop()
        
        try:
            async for chunk in audio_generator:
                if session.is_interrupted:
                    logger.info("[AudioPlayer] Interrupt detected. Stopping playback.")
                    break
                
                if chunk:
                    # Offload strictly to standard thread pool executor
                    await loop.run_in_executor(None, self._sync_write, chunk)
                    
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error during playback: {e}")
        finally:
            await session.set_speaking(False)

    def stop(self):
        """Force stop logic if needed, typically handled by interrupts"""
        pass

    def terminate(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self._audio_interface.terminate()

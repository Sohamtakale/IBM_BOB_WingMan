# audio/mic_stream.py
import pyaudio
import asyncio
import logging

logger = logging.getLogger(__name__)

try:
    from reflex_loop import config
except ImportError:
    import config

class MicrophoneStream:
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self._audio_interface = pyaudio.PyAudio()
        self._buffer = asyncio.Queue()
        self.closed = True
        self.stream = None

    def __enter__(self):
        self.closed = False
        self.stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=getattr(config, "CHANNELS", 1),
            rate=getattr(config, "SAMPLE_RATE", 16000),
            input=True,
            frames_per_buffer=getattr(config, "CHUNK_SIZE", 480),
            stream_callback=self._fill_buffer,
        )
        return self

    def __exit__(self, type, value, traceback):
        self.closed = True
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self._audio_interface.terminate()

    def _fill_buffer(self, in_data, frame_count, time_info, status_flags):
        """Called from pyaudio's C thread. Push to asyncio queue safely."""
        self.loop.call_soon_threadsafe(self._buffer.put_nowait, in_data)
        return None, pyaudio.paContinue

    async def async_generator(self):
        while not self.closed:
            chunk = await self._buffer.get()
            if chunk is None:
                return
            data = [chunk]

            while not self._buffer.empty():
                try:
                    chunk = self._buffer.get_nowait()
                    if chunk is None:
                        return
                    data.append(chunk)
                except asyncio.QueueEmpty:
                    break

            yield b''.join(data)

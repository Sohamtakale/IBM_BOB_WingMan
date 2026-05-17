# tts_test.py
import asyncio
import json
import logging
from reflex_loop.tts.tts_client import TTSClient

logging.basicConfig(level=logging.DEBUG)

class SessionMock:
    is_interrupted = False

async def text_gen():
    yield 'Hello, this is a test of the Deepgram WebSocket. Can you hear me now?'

async def main():
    tts = TTSClient()
    session = SessionMock()
    count = 0
    try:
        async for chunk in tts.stream_audio(text_gen(), session):
            count += 1
            print(f'Received chunk {count} of size {len(chunk)}')
    except Exception as e:
        print(f"Exception during stream: {e}")

if __name__ == "__main__":
    asyncio.run(main())

# tts/tts_client.py
import os
import json
import asyncio
import logging
import websockets

try:
    from reflex_loop import config
except ImportError:
    import config

logger = logging.getLogger(__name__)

class TTSClient:
    def __init__(self):
        self.provider = config.TTS_PROVIDER

    async def stream_audio(self, text_iterator, session):
        """
        Consumes text_iterator (async generator of strings).
        Yields audio chunks (bytes).
        """
        logger.info(f"[TTS] Streaming audio via {self.provider}...")
        
        if self.provider == "deepgram":
            async for chunk in self._stream_deepgram_ws(text_iterator, session):
                yield chunk
        else:
            async for chunk in self._stream_dummy(text_iterator, session):
                yield chunk

    async def _stream_dummy(self, text_iterator, session):
        """Dummy TTS that just prints text and sleeps."""
        async for text in text_iterator:
            if session.is_interrupted:
                break
            logger.info(f"[TTS Dummy] 'Speaking': {text}")
            await asyncio.sleep(0.5)

    async def _stream_deepgram_ws(self, text_iterator, session):
        """Streams text dynamically into a persistent WebSocket and yields audio."""
        api_key = getattr(config, "DEEPGRAM_API_KEY", None)
        if not api_key:
            logger.error("[TTS] Invalid Deepgram API Key.")
            return

        voice = getattr(config, "TTS_VOICE", "aura-asteria-en")
        sample_rate = getattr(config, "SAMPLE_RATE", 16000)
        url = f"wss://api.deepgram.com/v1/speak?model={voice}&encoding=linear16&sample_rate={sample_rate}"
        
        headers = {"Authorization": f"Token {api_key}"}

        try:
            # For websockets >= 11 it is additional_headers
            async with websockets.connect(url, additional_headers=headers) as ws:
                
                async def sender():
                    try:
                        async for text_chunk in text_iterator:
                            if session.is_interrupted:
                                break
                            if text_chunk.strip():
                                await ws.send(json.dumps({"type": "Speak", "text": text_chunk}))
                        
                        if not session.is_interrupted:
                            await ws.send(json.dumps({"type": "Flush"}))
                            await ws.send(json.dumps({"type": "Close"}))
                    except Exception as e:
                        logger.error(f"[TTS] Sender WS Error: {e}")

                sender_task = asyncio.create_task(sender())

                try:
                    async for msg in ws:
                        if session.is_interrupted:
                            break
                        
                        if isinstance(msg, bytes):
                            yield msg
                        elif isinstance(msg, str):
                            data = json.loads(msg)
                            if data.get("type") == "Close":
                                break
                            elif data.get("type") == "Error":
                                logger.error(f"[TTS] Deepgram WS Error Response: {data}")
                                break
                except websockets.exceptions.ConnectionClosed:
                    logger.debug("[TTS] WebSocket connection closed explicitly.")
                finally:
                    sender_task.cancel()
                    
        except Exception as e:
            logger.error(f"[TTS] WebSocket Connection Error: {e}")

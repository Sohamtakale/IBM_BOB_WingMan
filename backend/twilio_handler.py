import os
import json
import base64
import asyncio
import logging
import re
from typing import Optional

try:
    import audioop
except ModuleNotFoundError:
    import audioop_lts as audioop  # Python 3.13+ compatibility
import httpx
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from twilio.rest import Client as TwilioClient
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from deepgram import DeepgramClient, LiveTranscriptionEvents, LiveOptions
from groq import AsyncGroq

from . import storage
from .models import CallStatus
from .coach import generate_coach_report

logger = logging.getLogger(__name__)
router = APIRouter()


async def send_whatsapp_summary(call_id: str, call_brief, transcript, user_profile):
    if not transcript:
        return

    name = user_profile.name if user_profile else "you"
    transcript_text = "\n".join([
        f"{'WingMan' if t.speaker == 'wingman' else call_brief.who_calling}: {t.text}"
        for t in transcript
    ])

    try:
        groq_client = AsyncGroq(api_key=GROQ_API_KEY)
        resp = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You write short WhatsApp summaries of phone calls. "
                        "Plain text only — no markdown, no asterisks, no bullet symbols. "
                        "Use numbered lists for action items. Keep it under 250 words."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Summarize this call for {name}.\n\n"
                        f"Message delivered to {call_brief.who_calling}: {call_brief.goal}\n\n"
                        f"Full transcript:\n{transcript_text}\n\n"
                        f"Write a WhatsApp message to {name} with:\n"
                        f"- One line: did the message land OK?\n"
                        f"- What {call_brief.who_calling} said / replied\n"
                        f"- Questions they asked that {name} needs to answer (if any)\n"
                        f"- Action items for {name} (if any)\n\n"
                        f"Start with: Call with {call_brief.who_calling} is done."
                    ),
                },
            ],
            max_tokens=350,
            temperature=0.3,
        )
        body = resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[{call_id}] WhatsApp LLM error: {e}")
        caller_lines = [t.text for t in transcript if t.speaker != "wingman"]
        body = (
            f"Call with {call_brief.who_calling} is done.\n\n"
            f"Your message: {call_brief.goal}\n\n"
            f"What they said:\n" + "\n".join(f"- {l}" for l in caller_lines)
        )

    try:
        twilio_client.messages.create(
            from_=WHATSAPP_FROM,
            to=WHATSAPP_TO,
            body=body,
        )
        logger.info(f"[{call_id}] WhatsApp summary sent to {WHATSAPP_TO}")
    except Exception as e:
        logger.error(f"[{call_id}] WhatsApp send error: {e}")


async def detect_caller_identity(utterance: str, expected_caller: str = "") -> Optional[str]:
    """
    Detect if the caller mentioned their name/identity in their utterance.
    Uses LLM to extract name from natural language patterns.
    
    Args:
        utterance: The caller's spoken text
        expected_caller: Optional hint about who we're calling (from call_brief)
    
    Returns:
        Detected name or None if no clear identification
    """
    try:
        groq_client = AsyncGroq(api_key=GROQ_API_KEY)
        
        prompt = f"""Extract the caller's name if they identify themselves in this utterance.

UTTERANCE: "{utterance}"

RULES:
- Return ONLY the name if they clearly identify themselves (e.g., "This is John", "Sarah speaking", "It's Mike")
- Return "unknown" if they don't identify themselves or just ask a question
- Return "unknown" if they mention someone else's name but not their own (e.g., "John told me to call")
- Include titles if mentioned (e.g., "Dr. Smith", "Professor Jones")
- Be conservative - only extract if you're confident it's self-identification

EXAMPLES:
"Hi, this is John Smith" → John Smith
"It's Sarah" → Sarah
"Dr. Johnson speaking" → Dr. Johnson
"Yeah, what's up?" → unknown
"John told me to call" → unknown
"Is this the right number?" → unknown

NAME:"""

        resp = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.1,
        )
        
        result = resp.choices[0].message.content.strip().strip('"\'')
        
        # Clean up the result
        if result.lower() in ["unknown", "none", "n/a", ""]:
            return None
        
        # Basic validation - name should be reasonable length
        if len(result) > 50 or len(result) < 2:
            return None
            
        return result
        
    except Exception as e:
        logger.error(f"Caller identity detection error: {e}")
        return None


DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
WHATSAPP_FROM = os.getenv("WHATSAPP_FROM", "whatsapp:+14155238886")  # Twilio sandbox
WHATSAPP_TO = os.getenv("WHATSAPP_TO", "whatsapp:+917058809304")

twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# track active call websockets for mid-call override
active_websockets: dict = {}


def build_system_prompt(call_brief, user_profile) -> str:
    name = user_profile.name if user_profile else "the user"
    recipient = call_brief.who_calling or "them"
    message = call_brief.goal

    return f"""You are WingMan — a smart, warm AI assistant making a call on behalf of {name}.

SITUATION:
- You called {recipient} on behalf of {name}.
- The message you already delivered to them: "{message}"
- You already asked if they have anything to say or ask {name}.
- Now you're having a back-and-forth conversation with {recipient}.

HOW TO HANDLE QUESTIONS:
- Use common sense. If {name}'s message gives enough context to answer, answer it naturally.
- If they ask something personal about {name} that the message doesn't cover, say "I'm not sure — I'll let {name} know you asked."
- Never make up specific facts. Never say things like "that's their favorite color" unless the message says so.
- If they want to change something (time, place, plans), acknowledge it and confirm you'll pass it along.
- Keep each reply short — 1 to 3 sentences max.

CRITICAL — KEEP THE CONVERSATION OPEN:
- After EVERY answer, end with a short open invitation like "Anything else?" or "What else is on your mind?" or "Is there anything else you'd like me to pass along?"
- This tells them they can keep talking. Without it, they'll assume the call is over and hang up.
- Never go silent after answering. Always hand the floor back to them.

ENDING THE CALL:
- Only say "Goodbye!" when they clearly say they're done (e.g. "no that's all", "thanks bye", "I'm good").
- Do NOT rush to end. Keep going as long as they have questions."""


def detect_dtmf(text: str) -> Optional[str]:
    word_map = {
        "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
        "six": "6", "seven": "7", "eight": "8", "nine": "9", "zero": "0",
        "pound": "#", "star": "*",
    }
    patterns = [
        r"press\s+(\d)",
        r"press\s+(one|two|three|four|five|six|seven|eight|nine|zero|pound|star)",
        r"dial\s+(\d)",
        r"enter\s+(\d)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            digit = match.group(1)
            return word_map.get(digit, digit)
    return None


def split_into_sentences(text: str) -> list[str]:
    """
    Split text into complete sentences for streaming TTS.
    Preserves incomplete sentences at the end.
    """
    # Pattern matches sentence endings: . ! ? followed by space/newline
    pattern = r'([.!?]+(?:\s+|$))'
    parts = re.split(pattern, text)
    
    sentences = []
    current = ""
    
    for i, part in enumerate(parts):
        current += part
        # If this part is a sentence ending and we have enough content
        if re.match(pattern, part) and len(current.strip()) >= 10:
            sentences.append(current.strip())
            current = ""
    
    # Add remaining text as incomplete sentence (will be completed later)
    if current.strip():
        sentences.append(current.strip())
    
    return sentences if sentences else [text]


async def generate_tts_audio(text: str) -> bytes:
    """Generate TTS audio for a complete text (legacy non-streaming)"""
    url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en&encoding=linear16&sample_rate=8000"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, headers=headers, json={"text": text})
        if resp.status_code == 200:
            return resp.content
        logger.error(f"TTS error {resp.status_code}: {resp.text[:200]}")
        return b""


async def generate_and_send_tts(
    text: str,
    stream_sid: str,
    websocket: WebSocket,
    call_id: str,
    sequence_num: int
) -> bool:
    """
    Generate TTS audio for a sentence and send it to Twilio immediately.
    Returns True if successful, False otherwise.
    """
    try:
        audio_bytes = await generate_tts_audio(text)
        logger.info(f"[{call_id}] TTS #{sequence_num} got {len(audio_bytes)} bytes for: {text[:40]!r}")
        
        if audio_bytes and stream_sid:
            # Ensure even byte count for 16-bit PCM conversion
            if len(audio_bytes) % 2:
                audio_bytes = audio_bytes[:-1]
            mulaw_audio = pcm16_to_mulaw(audio_bytes)
            
            # Send in 160-byte chunks (20ms each)
            for i in range(0, len(mulaw_audio), 160):
                chunk = mulaw_audio[i:i + 160]
                await websocket.send_text(json.dumps({
                    "event": "media",
                    "streamSid": stream_sid,
                    "media": {"payload": base64.b64encode(chunk).decode()},
                }))
            
            logger.info(f"[{call_id}] TTS #{sequence_num} sent {len(mulaw_audio)} mulaw bytes")
            return True
        return False
    except Exception as e:
        logger.error(f"[{call_id}] TTS #{sequence_num} error: {e}", exc_info=True)
        return False


def pcm16_to_mulaw(pcm_data: bytes) -> bytes:
    return audioop.lin2ulaw(pcm_data, 2)


@router.post("/voice/{call_id}")
async def voice_webhook(call_id: str, request: Request):
    base_ws_url = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")
    response = VoiceResponse()
    connect = Connect()
    connect.stream(url=f"{base_ws_url}/twilio/media-stream/{call_id}")
    response.append(connect)
    return PlainTextResponse(str(response), media_type="text/xml")


async def _detect_and_store_caller(call_id: str, utterance: str, expected_caller: str):
    detected_name = await detect_caller_identity(utterance, expected_caller)
    if detected_name:
        storage.set_caller_name(call_id, detected_name)
        logger.info(f"[{call_id}] Detected caller name: {detected_name}")


@router.websocket("/media-stream/{call_id}")
async def media_stream_ws(websocket: WebSocket, call_id: str):
    await websocket.accept()
    active_websockets[call_id] = websocket

    call = storage.get_call(call_id)
    if not call:
        await websocket.close()
        return

    storage.update_call_status(call_id, CallStatus.IN_PROGRESS)
    loop = asyncio.get_event_loop()

    transcript_queue: asyncio.Queue = asyncio.Queue()
    tts_queue: asyncio.Queue = asyncio.Queue()

    stream_sid: Optional[str] = None
    conversation_history = []
    system_prompt = build_system_prompt(call.call_brief, call.user_profile)
    pending_utterance = ""
    is_goal_done = False

    # --- Deepgram STT setup ---
    dg_client = DeepgramClient(DEEPGRAM_API_KEY)
    dg_connection = dg_client.listen.live.v("1")

    def on_transcript(conn, result, **kwargs):
        try:
            if result.channel and result.channel.alternatives:
                text = result.channel.alternatives[0].transcript
                if text:
                    asyncio.run_coroutine_threadsafe(
                        transcript_queue.put({
                            "type": "transcript",
                            "text": text,
                            "is_final": result.is_final,
                        }),
                        loop,
                    )
        except Exception as e:
            logger.error(f"[{call_id}] Transcript cb error: {e}")

    def on_utterance_end(conn, **kwargs):
        asyncio.run_coroutine_threadsafe(
            transcript_queue.put({"type": "utterance_end", "text": "", "is_final": True}),
            loop,
        )

    dg_connection.on(LiveTranscriptionEvents.Transcript, on_transcript)
    dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, on_utterance_end)

    options = LiveOptions(
        model="nova-2",
        encoding="mulaw",
        sample_rate=8000,
        channels=1,
        smart_format=True,
        interim_results=True,
        endpointing=800,       # wait longer before finalizing speech
        vad_events=True,
        utterance_end_ms=2500, # give caller more time to finish speaking
    )
    dg_connection.start(options)

    # --- Transcript → LLM → TTS queue ---
    async def process_loop():
        nonlocal pending_utterance, is_goal_done
        groq_client = AsyncGroq(api_key=GROQ_API_KEY)

        while True:
            payload = await transcript_queue.get()
            text = payload.get("text", "").strip()
            is_final = payload.get("is_final", False)

            if text:
                pending_utterance = text

            # Only fire on real final transcripts with actual words.
            # utterance_end arrives with is_final=True but empty text — skip it.
            if not (is_final and text and not is_goal_done):
                continue

            utterance = text
            pending_utterance = ""

            storage.add_transcript_turn(call_id, "caller", utterance)
            logger.info(f"[{call_id}] CALLER: {utterance}")

            # Fire-and-forget caller identity detection on first turn only
            current_call = storage.get_call(call_id)
            if current_call and current_call.detected_caller_name is None:
                caller_turns = [t for t in current_call.transcript if t.speaker == "caller"]
                if len(caller_turns) == 1:
                    asyncio.create_task(_detect_and_store_caller(call_id, utterance, current_call.call_brief.who_calling))

            conversation_history.append({"role": "user", "content": utterance})
            messages = [{"role": "system", "content": system_prompt}] + conversation_history[-12:]

            try:
                resp = await groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=messages,
                    temperature=0.6,
                    max_tokens=150,
                    stream=False,
                )
                response_text = resp.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"[{call_id}] LLM error: {e}")
                response_text = "I'm sorry, could you repeat that?"

            conversation_history.append({"role": "assistant", "content": response_text})
            storage.add_transcript_turn(call_id, "wingman", response_text)
            logger.info(f"[{call_id}] WINGMAN: {response_text}")

            if response_text.lower().rstrip("!. ").endswith("goodbye"):
                is_goal_done = True
                storage.update_call_status(call_id, CallStatus.COMPLETING)

            await tts_queue.put(response_text)

    # --- TTS → Twilio audio ---
    async def tts_loop():
        nonlocal stream_sid
        while True:
            text = await tts_queue.get()
            try:
                audio_bytes = await generate_tts_audio(text)
                logger.info(f"[{call_id}] TTS got {len(audio_bytes)} bytes for: {text[:40]!r}")
                if audio_bytes and stream_sid:
                    if len(audio_bytes) % 2:
                        audio_bytes = audio_bytes[:-1]
                    mulaw_audio = pcm16_to_mulaw(audio_bytes)
                    for i in range(0, len(mulaw_audio), 160):
                        chunk = mulaw_audio[i:i + 160]
                        await websocket.send_text(json.dumps({
                            "event": "media",
                            "streamSid": stream_sid,
                            "media": {"payload": base64.b64encode(chunk).decode()},
                        }))
                    logger.info(f"[{call_id}] TTS sent {len(mulaw_audio)} mulaw bytes in chunks")
            except Exception as e:
                logger.error(f"[{call_id}] TTS loop error: {e}", exc_info=True)

    process_task = asyncio.create_task(process_loop())
    tts_task = asyncio.create_task(tts_loop())

    try:
        async for raw_msg in websocket.iter_text():
            data = json.loads(raw_msg)
            event = data.get("event")

            if event == "start":
                stream_sid = data["start"]["streamSid"]
                logger.info(f"[{call_id}] Stream started: {stream_sid}")
                # WingMan opens the call
                user_name = call.user_profile.name if call.user_profile else "the user"
                opening = f"Hi! I'm WingMan, {user_name}'s AI assistant. {call.call_brief.goal} Is there anything you'd like to say or ask {user_name}?"
                storage.add_transcript_turn(call_id, "wingman", opening)
                conversation_history.append({"role": "assistant", "content": opening})
                await tts_queue.put(opening)

            elif event == "media":
                track = data.get("media", {}).get("track", "inbound")
                if track == "inbound":
                    audio_bytes = base64.b64decode(data["media"]["payload"])
                    dg_connection.send(audio_bytes)

            elif event == "stop":
                logger.info(f"[{call_id}] Stream stopped")
                break

    except WebSocketDisconnect:
        logger.info(f"[{call_id}] WebSocket disconnected")
    finally:
        process_task.cancel()
        tts_task.cancel()
        dg_connection.finish()

        current_call = storage.get_call(call_id)
        if current_call and current_call.transcript:
            try:
                coach = await generate_coach_report(
                    call_id,
                    current_call.transcript,
                    current_call.call_brief,
                    current_call.detected_caller_name
                )
                storage.save_coach_report(call_id, coach)
                storage.finalize_call(call_id, coach.summary)
            except Exception as e:
                logger.error(f"[{call_id}] Post-call processing error: {e}")
                storage.finalize_call(call_id, "Call completed.")

            # Send WhatsApp recap to user
            try:
                await send_whatsapp_summary(
                    call_id,
                    current_call.call_brief,
                    current_call.transcript,
                    current_call.user_profile,
                )
            except Exception as e:
                logger.error(f"[{call_id}] WhatsApp summary error: {e}")
        else:
            storage.finalize_call(call_id, "Call completed.")

        active_websockets.pop(call_id, None)
        logger.info(f"[{call_id}] Call session cleaned up")

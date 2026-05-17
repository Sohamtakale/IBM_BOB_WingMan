import os
import uuid
import logging
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from twilio.rest import Client as TwilioClient

from .models import StartCallRequest, UserProfile, CoPilotRequest, CallStatus
from . import storage
from .twilio_handler import router as twilio_router
from .copilot import get_suggestions
from .coach import generate_coach_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("wingman")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

app = FastAPI(title="WingMan API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(twilio_router, prefix="/twilio")


@app.get("/health")
def health():
    return {"status": "ok", "service": "WingMan", "base_url": BASE_URL}


# --- Profile ---

@app.get("/profile")
def get_profile():
    profile = storage.get_profile()
    return profile or UserProfile()


@app.post("/profile")
def save_profile(profile: UserProfile):
    storage.save_profile(profile)
    return {"status": "saved"}


# --- AutoPilot ---

@app.post("/autopilot/start")
async def start_autopilot_call(request: StartCallRequest):
    call_id = str(uuid.uuid4())
    profile = request.user_profile or storage.get_profile()

    storage.create_call(call_id, request.phone_number, request.call_brief, profile)

    webhook_url = f"{BASE_URL}/twilio/voice/{call_id}"
    logger.info(f"Twilio webhook URL: {webhook_url}")

    try:
        call = twilio_client.calls.create(
            to=request.phone_number,
            from_=TWILIO_PHONE_NUMBER,
            url=webhook_url,
            method="POST",
        )
        storage.set_twilio_sid(call_id, call.sid)
        logger.info(f"Call initiated: {call_id} → {request.phone_number} (SID: {call.sid})")
    except Exception as e:
        storage.update_call_status(call_id, CallStatus.FAILED)
        raise HTTPException(status_code=500, detail=f"Twilio error: {str(e)}")

    return {"call_id": call_id, "status": "initiating", "twilio_sid": call.sid}


# --- Calls ---

@app.get("/calls")
def list_calls():
    return storage.get_all_calls()


@app.get("/calls/{call_id}")
def get_call(call_id: str):
    call = storage.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    return call


@app.post("/calls/{call_id}/end")
async def end_call(call_id: str):
    call = storage.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    if call.twilio_call_sid:
        try:
            twilio_client.calls(call.twilio_call_sid).update(status="completed")
        except Exception as e:
            logger.error(f"Error ending Twilio call: {e}")
    storage.update_call_status(call_id, CallStatus.COMPLETED)
    return {"status": "ended"}


@app.get("/calls/{call_id}/coach")
async def get_coach_report(call_id: str):
    call = storage.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    if call.coach_report:
        return call.coach_report
    if call.transcript:
        report = await generate_coach_report(call_id, call.transcript, call.call_brief)
        storage.save_coach_report(call_id, report)
        return report
    raise HTTPException(status_code=404, detail="No transcript available yet")


# --- Co-Pilot ---

@app.post("/copilot/suggest")
async def copilot_suggest(request: CoPilotRequest):
    return await get_suggestions(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

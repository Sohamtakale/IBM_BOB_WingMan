from typing import Dict, Optional, List
from datetime import datetime
from .models import CallRecord, CallBrief, CallStatus, TranscriptTurn, CoachReport, UserProfile

_calls: Dict[str, CallRecord] = {}
_user_profile: Optional[UserProfile] = None


def create_call(call_id: str, phone_number: str, call_brief: CallBrief, profile: Optional[UserProfile] = None) -> CallRecord:
    record = CallRecord(
        call_id=call_id,
        phone_number=phone_number,
        call_brief=call_brief,
        user_profile=profile,
        status=CallStatus.INITIATING,
        transcript=[],
        started_at=datetime.now(),
    )
    _calls[call_id] = record
    return record


def get_call(call_id: str) -> Optional[CallRecord]:
    return _calls.get(call_id)


def get_all_calls() -> List[CallRecord]:
    return list(reversed(list(_calls.values())))


def update_call_status(call_id: str, status: CallStatus):
    if call_id in _calls:
        _calls[call_id].status = status


def set_twilio_sid(call_id: str, twilio_sid: str):
    if call_id in _calls:
        _calls[call_id].twilio_call_sid = twilio_sid


def add_transcript_turn(call_id: str, speaker: str, text: str):
    if call_id in _calls:
        _calls[call_id].transcript.append(TranscriptTurn(
            speaker=speaker,
            text=text,
            timestamp=datetime.now(),
        ))


def finalize_call(call_id: str, summary: str = ""):
    if call_id in _calls:
        _calls[call_id].status = CallStatus.COMPLETED
        _calls[call_id].ended_at = datetime.now()
        _calls[call_id].summary = summary


def save_coach_report(call_id: str, report: CoachReport):
    if call_id in _calls:
        _calls[call_id].coach_report = report


def set_caller_name(call_id: str, name: Optional[str]):
    if call_id in _calls and name:
        _calls[call_id].detected_caller_name = name


def get_profile() -> Optional[UserProfile]:
    return _user_profile


def save_profile(profile: UserProfile):
    global _user_profile
    _user_profile = profile

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserProfile(BaseModel):
    name: str = ""
    profession: str = ""
    institution: str = ""
    communication_style: str = "Professional"
    languages: str = "English"
    default_tone: str = "Professional"


class CallBrief(BaseModel):
    who_calling: str
    goal: str
    key_points: str = ""
    questions_to_ask: str = ""
    things_to_avoid: str = ""
    tone: str = "Professional"


class StartCallRequest(BaseModel):
    phone_number: str
    call_brief: CallBrief
    user_profile: Optional[UserProfile] = None


class TranscriptTurn(BaseModel):
    speaker: str  # "caller" or "wingman"
    text: str
    timestamp: datetime


class CallStatus(str, Enum):
    INITIATING = "initiating"
    IN_PROGRESS = "in_progress"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"


class CoachReport(BaseModel):
    call_id: str
    confidence_score: int
    what_went_well: List[str]
    what_to_improve: List[str]
    improvements: List[str]
    goal_achieved: bool
    goal_achievement_score: int
    summary: str = ""


class CallRecord(BaseModel):
    call_id: str
    phone_number: str
    call_brief: CallBrief
    user_profile: Optional[UserProfile] = None
    status: CallStatus = CallStatus.INITIATING
    transcript: List[TranscriptTurn] = []
    summary: str = ""
    twilio_call_sid: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    coach_report: Optional[CoachReport] = None
    detected_caller_name: Optional[str] = None


class CoPilotRequest(BaseModel):
    transcript: str
    call_brief: Optional[CallBrief] = None
    conversation_history: Optional[List[dict]] = []


class CoPilotSuggestion(BaseModel):
    tone: str
    text: str
    confidence: int


class CoPilotResponse(BaseModel):
    intent: str
    suggestions: List[CoPilotSuggestion]

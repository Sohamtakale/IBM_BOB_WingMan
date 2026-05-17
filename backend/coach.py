import os
import json
import logging
from typing import List, Optional
from groq import AsyncGroq
from .models import CoachReport, TranscriptTurn, CallBrief

logger = logging.getLogger(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


async def generate_coach_report(
    call_id: str,
    transcript: List[TranscriptTurn],
    call_brief: CallBrief,
    detected_caller_name: Optional[str] = None
) -> CoachReport:
    if not transcript:
        return CoachReport(
            call_id=call_id,
            confidence_score=0,
            what_went_well=[],
            what_to_improve=["No conversation was recorded"],
            improvements=["Ensure the call connected properly before analyzing"],
            goal_achieved=False,
            goal_achievement_score=0,
            summary="No conversation was recorded for this call.",
        )

    transcript_text = "\n".join([f"{t.speaker.upper()}: {t.text}" for t in transcript])

    # Add caller identity context if detected
    caller_context = ""
    if detected_caller_name:
        caller_context = f"DETECTED CALLER IDENTITY: {detected_caller_name}\n"

    client = AsyncGroq(api_key=GROQ_API_KEY)
    prompt = (
        f"Analyze this phone call transcript and produce a coaching report.\n\n"
        f"CALL GOAL: {call_brief.goal}\n"
        f"EXPECTED CALLER: {call_brief.who_calling}\n"
        f"{caller_context}"
        f"QUESTIONS TO ASK: {call_brief.questions_to_ask}\n"
        f"THINGS TO AVOID: {call_brief.things_to_avoid}\n\n"
        f"TRANSCRIPT:\n{transcript_text}\n\n"
        f"Return ONLY valid JSON (no markdown):\n"
        f'{{"confidence_score": <0-100>, "goal_achieved": <true/false>, '
        f'"goal_achievement_score": <0-100>, "summary": "<2-3 sentences>", '
        f'"what_went_well": ["<moment 1>", "<moment 2>"], '
        f'"what_to_improve": ["<weakness 1>", "<weakness 2>"], '
        f'"improvements": ["<tip 1>", "<tip 2>", "<tip 3>"]}}'
    )

    try:
        resp = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.3,
        )
        raw = resp.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
        return CoachReport(
            call_id=call_id,
            confidence_score=int(data.get("confidence_score", 70)),
            what_went_well=data.get("what_went_well", []),
            what_to_improve=data.get("what_to_improve", []),
            improvements=data.get("improvements", []),
            goal_achieved=bool(data.get("goal_achieved", False)),
            goal_achievement_score=int(data.get("goal_achievement_score", 50)),
            summary=data.get("summary", ""),
        )
    except Exception as e:
        logger.error(f"Coach report generation failed: {e}")
        return CoachReport(
            call_id=call_id,
            confidence_score=60,
            what_went_well=["Call was completed"],
            what_to_improve=["Could not generate detailed analysis"],
            improvements=["Review the transcript manually for insights"],
            goal_achieved=False,
            goal_achievement_score=50,
            summary="Automated analysis encountered an error. Please review the transcript.",
        )

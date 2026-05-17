import logging
from .models import CoPilotRequest, CoPilotResponse, CoPilotSuggestion
from .agents.pipeline import copilot_pipeline

logger = logging.getLogger(__name__)


async def get_suggestions(request: CoPilotRequest) -> CoPilotResponse:
    brief_goal = request.call_brief.goal if request.call_brief else "Have a productive conversation"
    brief_tone = request.call_brief.tone if request.call_brief else "Professional"

    state = {
        "transcript": request.transcript,
        "conversation_history": request.conversation_history or [],
        "call_brief_goal": brief_goal,
        "call_brief_tone": brief_tone,
        "intent": "",
        "suggestions": [],
    }

    result = await copilot_pipeline.ainvoke(state)

    return CoPilotResponse(
        intent=result["intent"],
        suggestions=[CoPilotSuggestion(**s) for s in result["suggestions"]],
    )

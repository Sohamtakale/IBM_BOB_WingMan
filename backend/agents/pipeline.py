import os
import json
import logging
from typing import TypedDict, List
from groq import AsyncGroq
from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class AgentState(TypedDict):
    transcript: str
    conversation_history: List[dict]
    call_brief_goal: str
    call_brief_tone: str
    intent: str
    suggestions: List[dict]


async def classifier_node(state: AgentState) -> AgentState:
    client = AsyncGroq(api_key=GROQ_API_KEY)
    prompt = (
        f"Classify the intent of this statement in ONE word from: "
        f"question, objection, small_talk, ivr, trap, statement\n\n"
        f'Statement: "{state["transcript"]}"\n\n'
        f"Respond with ONLY the intent word."
    )
    resp = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10,
        temperature=0.1,
    )
    intent = resp.choices[0].message.content.strip().lower()
    if intent not in ["question", "objection", "small_talk", "ivr", "trap", "statement"]:
        intent = "statement"
    return {**state, "intent": intent}


async def generator_node(state: AgentState) -> AgentState:
    client = AsyncGroq(api_key=GROQ_API_KEY)

    history_text = ""
    for turn in state["conversation_history"][-6:]:
        role = turn.get("role", "user").title()
        history_text += f"{role}: {turn.get('content', '')}\n"

    prompt = (
        f"You are a real-time conversation coach. Generate 3 response options.\n\n"
        f"Context:\n"
        f"- Goal: {state['call_brief_goal']}\n"
        f"- Tone: {state['call_brief_tone']}\n"
        f"- Intent detected: {state['intent']}\n"
        f"- Recent conversation:\n{history_text}\n"
        f'The other person just said: "{state["transcript"]}"\n\n'
        f"Generate exactly 3 responses as valid JSON (no markdown):\n"
        f'{{"confident": "...", "diplomatic": "...", "detailed": "..."}}'
    )

    resp = await client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.7,
    )

    try:
        raw = resp.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        data = json.loads(raw.strip())
        suggestions = [
            {"tone": "Confident", "text": data.get("confident", ""), "confidence": 90},
            {"tone": "Diplomatic", "text": data.get("diplomatic", ""), "confidence": 85},
            {"tone": "Detailed", "text": data.get("detailed", ""), "confidence": 80},
        ]
    except Exception as e:
        logger.warning(f"Generator parse error: {e}")
        suggestions = [
            {"tone": "Confident", "text": "I understand. Let me address that directly.", "confidence": 75},
            {"tone": "Diplomatic", "text": "That's a fair point. Here's my perspective.", "confidence": 70},
            {"tone": "Detailed", "text": "To fully answer that, let me explain.", "confidence": 65},
        ]

    return {**state, "suggestions": suggestions}


def build_copilot_pipeline():
    graph = StateGraph(AgentState)
    graph.add_node("classifier", classifier_node)
    graph.add_node("generator", generator_node)
    graph.add_edge("classifier", "generator")
    graph.add_edge("generator", END)
    graph.set_entry_point("classifier")
    return graph.compile()


copilot_pipeline = build_copilot_pipeline()

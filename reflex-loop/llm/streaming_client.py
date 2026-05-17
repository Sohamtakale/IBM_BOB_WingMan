# llm/streaming_client.py
import os
import asyncio
import logging

try:
    from reflex_loop import config
except ImportError:
    import config

logger = logging.getLogger(__name__)

class ConversationMemory:
    def __init__(self, system_prompt, max_turns=10):
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self.turns = []
        self.summary = ""

    def append(self, role, text, interrupted=False):
        if interrupted:
            text += " [INTERRUPTED]"
        self.turns.append({"role": role, "parts": [text]})
        if len(self.turns) > self.max_turns:
            self._compress()

    def _compress(self):
        # Move oldest 4 turns into the rolling summary to preserve context window length
        old_turns = self.turns[:4]
        self.turns = self.turns[4:]
        for t in old_turns:
            self.summary += f" {t['role']}: {t['parts'][0]}\n"

    def get_gemini_context(self):
        sys_prompt = self.system_prompt
        if self.summary:
            sys_prompt += f"\n\n[Previous conversation summary]:\n{self.summary}"
        return [{"role": "user", "parts": [sys_prompt]}, {"role": "model", "parts": ["Understood."]}] + self.turns

    def get_groq_messages(self):
        msgs = [{"role": "system", "content": self.system_prompt}]
        if self.summary:
            msgs[0]["content"] += f"\n\n[Previous conversation summary]:\n{self.summary}"
            
        for t in self.turns:
            r = "assistant" if t["role"] == "model" else "user"
            msgs.append({"role": r, "content": t["parts"][0]})
        return msgs

class LLMClient:
    def __init__(self):
        self.provider = getattr(config, "LLM_PROVIDER", "groq")
        self.model = None
        self.groq_client = None

        logger.info(f"[LLM] Initializing {self.provider} client...")

        if self.provider == "gemini":
            try:
                import google.generativeai as genai
                api_key = getattr(config, "GEMINI_API_KEY", None)
                if not api_key:
                    logger.warning("[LLM] Warning: Gemini API Key not set.")
                else:
                    genai.configure(api_key=api_key)
                    self.model = genai.GenerativeModel('gemini-2.5-flash')
                    logger.info("[LLM] Initialized Gemini 2.5 Flash")
            except Exception as e:
                logger.error(f"[LLM] Error initializing Gemini: {e}")

        elif self.provider == "groq":
            try:
                from groq import AsyncGroq
                api_key = getattr(config, "GROQ_API_KEY", None)
                if not api_key:
                    logger.warning("[LLM] Warning: GROQ_API_KEY not set.")
                else:
                    self.groq_client = AsyncGroq(api_key=api_key)
                    logger.info("[LLM] Initialized AsyncGroq Client")
            except Exception as e:
                logger.error(f"[LLM] Error initializing Groq: {e}")

    async def stream_chat(self, memory: ConversationMemory, session, memory_manager=None):
        if self.provider == "gemini":
             async for token in self._stream_gemini(memory, session, memory_manager):
                 yield token
        elif self.provider == "groq":
             async for token in self._stream_groq(memory, session, memory_manager):
                 yield token
        else:
             async for token in self._stream_dummy(memory, session):
                 yield token

    async def _stream_dummy(self, memory, session):
        yield "Dummy response."

    async def _stream_gemini(self, memory, session, memory_manager=None):
        if session.is_interrupted: return
        if not self.model:
            yield "I can't think right now."
            return

        try:
            full_context = memory.get_gemini_context()
            user_msg = full_context[-1]['parts'][0]
            context_history = full_context[:-1]
            
            # Retrieve injected multimodal memory if available
            if memory_manager:
                extra_context = await asyncio.to_thread(memory_manager.retrieve_context, user_msg)
                if extra_context:
                    user_msg += extra_context
            
            chat = self.model.start_chat(history=context_history)
            
            response = await asyncio.to_thread(chat.send_message, user_msg, stream=True)
            
            for chunk in response:
                if session.is_interrupted: break
                if chunk.text:
                    yield chunk.text
                    await asyncio.sleep(0) # Yield control
        except Exception as e:
            logger.error(f"[LLM] Gemini Error: {e}")
            yield "Sorry, I lost my train of thought."

    async def _stream_groq(self, memory, session, memory_manager=None):
        if session.is_interrupted: return
        if not self.groq_client:
            yield "Groq not initialized."
            return
        
        try:
            groq_messages = memory.get_groq_messages()
            
            # Retrieve injected multimodal memory if available
            if memory_manager and len(memory.turns) > 0:
                latest_query = memory.turns[-1]["parts"][0]
                extra_context = await asyncio.to_thread(memory_manager.retrieve_context, latest_query)
                if extra_context:
                    # Append it to the last user message
                    groq_messages[-1]["content"] += extra_context

            completion = await self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=groq_messages,
                temperature=getattr(config, "TEMPERATURE", 0.7),
                max_tokens=getattr(config, "MAX_TOKENS", 150),
                stream=True,
            )

            async for chunk in completion:
                if session.is_interrupted: break
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    yield token

        except Exception as e:
            logger.error(f"[LLM] Groq Error: {e}")
            yield "I lost connection."

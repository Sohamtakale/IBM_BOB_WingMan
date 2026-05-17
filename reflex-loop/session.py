# session.py
import asyncio
import uuid
import logging

logger = logging.getLogger(__name__)

class SessionContext:
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.bot_is_speaking = False
        self.interrupt_flag = False
        self._lock = asyncio.Lock()
        
    async def set_speaking(self, is_speaking: bool):
        async with self._lock:
            self.bot_is_speaking = is_speaking

    async def trigger_interrupt(self):
        async with self._lock:
            self.interrupt_flag = True
            logger.warning(f"[{self.session_id}] INTERRUPT TRIGGERED")

    async def clear_interrupt(self):
        async with self._lock:
            self.interrupt_flag = False

    @property
    def is_interrupted(self) -> bool:
        # For fast sync reads, though setting is async
        return self.interrupt_flag
        
    @property
    def is_speaking(self) -> bool:
        # For fast sync reads
        return self.bot_is_speaking

# state.py
import threading
from dataclasses import dataclass, field
from typing import Optional, Any

@dataclass
class GlobalState:
    """
    Thread-safe global state for the eFLEX LOOP system.
    """
    bot_is_speaking: bool = False
    interrupt_flag: bool = False
    active_llm_request: Optional[Any] = None
    active_tts_request: Optional[Any] = None
    
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def set_speaking(self, is_speaking: bool):
        with self._lock:
            self.bot_is_speaking = is_speaking

    def is_speaking(self) -> bool:
        with self._lock:
            return self.bot_is_speaking

    def trigger_interrupt(self):
        with self._lock:
            self.interrupt_flag = True
            # Logic to cancel requests would be triggered here or monitored by loops
            print("!!! INTERRUPT TRIGGERED !!!")

    def clear_interrupt(self):
        with self._lock:
            self.interrupt_flag = False
            
    def is_interrupted(self) -> bool:
        with self._lock:
            return self.interrupt_flag

# Singleton instance
state = GlobalState()

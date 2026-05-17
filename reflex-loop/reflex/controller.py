# reflex/controller.py
import sys
import os
import threading

# Add parent directory to path to import config/state
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from state import state
import config

class ReflexController:
    """
    The 'Nervous System'.
    Monitors state and triggers interrupts.
    In a full implementation, this might run a separate thread to monitor complex conditions,
    but for now it provides the trigger mechanism used by the VAD loop.
    """
    def __init__(self):
        pass

    def interrupt(self):
        """
        Trigger the system-wide interrupt.
        """
        if state.is_speaking() and not state.is_interrupted():
            print(">>> REFLEX: INTERRUPT TRIGGERED <<<")
            state.trigger_interrupt()
            # In a more complex setup, we might actively cancel requests here/futures.
            # For now, the flags will stop the loops.
            
    def clear(self):
        state.clear_interrupt()

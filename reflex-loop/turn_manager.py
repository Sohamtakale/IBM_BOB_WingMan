import re
import logging

logger = logging.getLogger(__name__)

class TurnManager:
    def __init__(self):
        # Words that indicate the user is just listening, NOT interrupting
        self.backchannels = re.compile(r'^(yeah|yep|mhm|uh huh|right|okay|cool|ah|oh)\.?$', re.IGNORECASE)

    def is_true_interruption(self, interim_text: str) -> bool:
        """
        Evaluates if the user's speech should cut off the bot.
        """
        cleaned = interim_text.strip().lower()
        if not cleaned:
            return False
            
        # If it's just a backchannel, ignore it.
        if self.backchannels.match(cleaned):
            return False
            
        # If it's a substantive word or phrase ("wait", "but", "no", etc.)
        # trigger an immediate halt.
        return True

import re
import emoji
import structlog
from backend.lystra.understanding.schemas import SemanticUnderstanding
from backend.config import get_settings

logger = structlog.get_logger(__name__)

# Fix #3: Add a regex pass for common ASCII emoticons
EMOTICON_PATTERN = re.compile(r'[:;=]-?[)(/DPp]')

class EmojiValidator:
    def _strip_all_emojis(self, text: str) -> str:
        """Helper to strip Unicode emojis and ASCII emoticons."""
        text = emoji.replace_emoji(text, replace="")
        text = EMOTICON_PATTERN.sub("", text)
        return text

    def _cap_emoji_density(self, text: str, max_emojis: int) -> str:
        """Caps the number of emojis in the text to `max_emojis`."""
        def replace_excess(matched_emoji, data_dict):
            replace_excess.count += 1
            if replace_excess.count > max_emojis:
                return ""
            return matched_emoji
            
        replace_excess.count = 0
        return emoji.replace_emoji(text, replace=replace_excess)

    def validate_and_clean(self, generated_text: str, understanding: SemanticUnderstanding) -> str:
        """
        Advanced Contextual Emoji Intelligence (Phase 17 Validation)
        Strips or modifies emojis after generation if they violate strict semantic rules.
        """
        # Fix #1: Use safe getattr/Enum access
        sensitivity = getattr(understanding.subject_sensitivity, "value", understanding.subject_sensitivity)
        emotion = getattr(understanding.user_emotion, "value", understanding.user_emotion)
        
        # If strict sensitivity, physically strip all emojis regardless of what LLM generated
        if sensitivity == "high":
            logger.debug("emoji_stripped", reason="high_sensitivity")
            return self._strip_all_emojis(generated_text)
            
        # If the user is frustrated, strip emojis to prioritize empathy over decoration
        if emotion == "frustrated":
            logger.debug("emoji_stripped", reason="frustrated_user")
            return self._strip_all_emojis(generated_text)
            
        # Check density
        emoji_count = emoji.emoji_count(generated_text)
        max_density = getattr(get_settings(), "MAX_EMOJI_DENSITY", 3)
        
        if emotion != "celebratory" and emoji_count > max_density:
            # Fix #2 and #4: Cap instead of full strip, based on config
            # TODO: Intelligently prune emojis by type instead of just truncation
            logger.debug("emoji_density_capped", original_count=emoji_count, max_density=max_density)
            return self._cap_emoji_density(generated_text, max_density)
            
        return generated_text

import sys

content = '''import logging
from typing import Literal, Optional, TypedDict, Dict
from backend.lystra.understanding.schemas import SemanticUnderstanding
from backend.lystra.context.conversation_state import ConversationState

logger = logging.getLogger(__name__)

InformationState = Literal["known", "inferred", "uncertain", "missing", "invalid_input"]

class AmbiguityResult(TypedDict):
    """
    Result of ambiguity detection.
    is_ambiguous: True if the pipeline should halt for user clarification.
    state: The classification of the information completeness.
    clarification_needed: The exact string to prompt the user with, or None.
    """
    is_ambiguous: bool
    state: InformationState
    clarification_needed: Optional[str]

# Centralized copy for easy localization/A-B testing
CLARIFICATION_MESSAGES: Dict[str, str] = {
    "missing_topic": "I want to make sure I get this exactly right. Could you clarify {topic}?",
    "uncertain": "I have limited confidence in my assumption here. Could you provide a bit more detail?",
    "invalid_input": "I'm having trouble processing that cleanly. Could you rephrase your request?"
}

class AmbiguityDetector:
    def __init__(self, 
                 threshold: float = 0.7, 
                 context_dependency_threshold: float = 0.5, 
                 confidence_threshold: float = 0.4):
        self.threshold = threshold
        self.context_dependency_threshold = context_dependency_threshold
        self.confidence_threshold = confidence_threshold

    def _safe_float(self, val: any) -> Optional[float]:
        if val is None:
            return None
        try:
            f = float(val)
            return max(0.0, min(1.0, f))
        except (ValueError, TypeError):
            return None

    def check_ambiguity(self, understanding: SemanticUnderstanding, state: ConversationState) -> AmbiguityResult:
        """
        Phase 8 & 28: Ambiguity Detection & Hallucination Reduction
        Distinguishes known, inferred, uncertain, and missing information.
        
        Returns an AmbiguityResult dict containing:
        - is_ambiguous (bool): Whether the response should be halted for clarification.
        - state (InformationState): The derived state ('known', 'inferred', 'uncertain', 'missing', 'invalid_input').
        - clarification_needed (str | None): The message to display to the user.
        """
        # 1. Input Validation
        amb = self._safe_float(getattr(understanding, 'ambiguity', None))
        ctx_dep = self._safe_float(getattr(understanding, 'context_dependency', None))
        conf = self._safe_float(getattr(understanding, 'confidence', None))

        if amb is None or ctx_dep is None or conf is None:
            logger.warning("ambiguity_detector_invalid_inputs", 
                           extra={"ambiguity": amb, "context_dependency": ctx_dep, "confidence": conf})
            return {
                "is_ambiguous": True,
                "state": "invalid_input",
                "clarification_needed": CLARIFICATION_MESSAGES["invalid_input"]
            }

        topic_str = getattr(understanding, "topic", None) or "what you meant"

        # 2. Ambiguity Evaluation
        if amb > self.threshold:
            # High ambiguity, check if we can infer from context
            if ctx_dep > self.context_dependency_threshold and getattr(state, 'current_topic', None):
                # Ensure we also have reasonable confidence before accepting inference
                if conf >= self.confidence_threshold:
                    logger.debug("ambiguity_detector_inferred", 
                                 extra={"ambiguity": amb, "context": ctx_dep, "confidence": conf})
                    return {"is_ambiguous": False, "state": "inferred", "clarification_needed": None}
            
            logger.info("ambiguity_detector_missing", 
                        extra={"ambiguity": amb, "context": ctx_dep, "confidence": conf})
            return {
                "is_ambiguous": True,
                "state": "missing",
                "clarification_needed": CLARIFICATION_MESSAGES["missing_topic"].format(topic=topic_str)
            }
            
        # 3. Uncertainty Evaluation
        if not getattr(understanding, 'is_fallback', False) and conf < self.confidence_threshold:
            logger.info("ambiguity_detector_uncertain", 
                        extra={"ambiguity": amb, "context": ctx_dep, "confidence": conf})
            return {
                "is_ambiguous": True,
                "state": "uncertain",
                "clarification_needed": CLARIFICATION_MESSAGES["uncertain"]
            }
            
        # 4. Known/Confident State
        logger.debug("ambiguity_detector_known", 
                     extra={"ambiguity": amb, "context": ctx_dep, "confidence": conf})
        return {"is_ambiguous": False, "state": "known", "clarification_needed": None}
'''

with open('backend/lystra/reasoning/ambiguity_detector.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("ambiguity_detector.py patched")

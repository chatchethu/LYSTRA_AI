import structlog
from typing import Literal, Optional, TypedDict, Dict, Any
from backend.lystra.understanding.schemas import SemanticUnderstanding
from backend.lystra.context.conversation_state import ConversationState
from backend.config import get_settings

logger = structlog.get_logger("lystra.ambiguity_detector")

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
    "missing_information": "I want to make sure I get this exactly right. Could you clarify {topic}?",
    "uncertain": "I have limited confidence in my assumption here. Could you provide a bit more detail?",
    "invalid_input": "I'm having trouble processing that cleanly. Could you rephrase your request?"
}

class AmbiguityDetector:
    def __init__(self, 
                 threshold: Optional[float] = None, 
                 context_dependency_threshold: Optional[float] = None, 
                 confidence_threshold: Optional[float] = None):
        settings = get_settings()
        self.threshold = threshold if threshold is not None else settings.AMBIGUITY_THRESHOLD
        self.context_dependency_threshold = context_dependency_threshold if context_dependency_threshold is not None else settings.AMBIGUITY_CONTEXT_THRESHOLD
        self.confidence_threshold = confidence_threshold if confidence_threshold is not None else settings.AMBIGUITY_CONFIDENCE_THRESHOLD

    def _safe_float(self, val: Any) -> Optional[float]:
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
        # 1. Fallback / Hard Failure Handling
        # When semantic analysis fails (timeout, bad JSON, LLM error), the understanding
        # is marked is_fallback=True. In this case we must NOT block with a clarification
        # request — the user said something real, we just couldn't parse it deeply.
        # Let the response proceed with best-effort context from conversation history.
        if getattr(understanding, 'is_fallback', False):
            logger.info("ambiguity_detector_fallback_input", 
                        failure_reason=getattr(understanding, 'failure_reason', None))
            return {
                "is_ambiguous": False,
                "state": "inferred",
                "clarification_needed": None
            }

        # 2. Input Validation
        amb = self._safe_float(getattr(understanding, 'ambiguity', None))
        ctx_dep = self._safe_float(getattr(understanding, 'context_dependency', None))
        conf = self._safe_float(getattr(understanding, 'confidence', None))

        if amb is None or ctx_dep is None or conf is None:
            logger.warning("ambiguity_detector_invalid_inputs", 
                           ambiguity=amb, context_dependency=ctx_dep, confidence=conf)
            return {
                "is_ambiguous": True,
                "state": "invalid_input",
                "clarification_needed": CLARIFICATION_MESSAGES["invalid_input"]
            }

        raw_topic = getattr(understanding, "topic", None)
        topic_str = raw_topic if raw_topic and raw_topic != "unknown" else "what you meant"

        # 3. Ambiguity Evaluation
        if amb > self.threshold:
            # High ambiguity, check if we can infer from context
            if ctx_dep > self.context_dependency_threshold and getattr(state, 'current_topic', None):
                # Ensure we also have reasonable confidence before accepting inference
                if conf >= self.confidence_threshold:
                    logger.debug("ambiguity_detector_inferred", 
                                 ambiguity=amb, context=ctx_dep, confidence=conf)
                    return {"is_ambiguous": False, "state": "inferred", "clarification_needed": None}
            
            logger.info("ambiguity_detector_missing", 
                        ambiguity=amb, context=ctx_dep, confidence=conf)
            return {
                "is_ambiguous": True,
                "state": "missing",
                "clarification_needed": CLARIFICATION_MESSAGES["missing_information"].format(topic=topic_str)
            }
            
        # 4. Uncertainty Evaluation
        if conf < self.confidence_threshold:
            logger.info("ambiguity_detector_uncertain", 
                        ambiguity=amb, context=ctx_dep, confidence=conf)
            return {
                "is_ambiguous": True,
                "state": "uncertain",
                "clarification_needed": CLARIFICATION_MESSAGES["uncertain"]
            }
            
        # 5. Known/Confident State
        logger.debug("ambiguity_detector_known", 
                     ambiguity=amb, context=ctx_dep, confidence=conf)
        return {"is_ambiguous": False, "state": "known", "clarification_needed": None}

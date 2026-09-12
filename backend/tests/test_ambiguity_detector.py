import pytest
from backend.lystra.reasoning.ambiguity_detector import AmbiguityDetector, CLARIFICATION_MESSAGES
from backend.lystra.understanding.schemas import SemanticUnderstanding
from backend.lystra.context.conversation_state import ConversationState

class DummyUnderstanding:
    def __init__(self, ambiguity, context_dependency, confidence, topic=None, is_fallback=False):
        self.ambiguity = ambiguity
        self.context_dependency = context_dependency
        self.confidence = confidence
        self.topic = topic
        self.is_fallback = is_fallback

class DummyState:
    def __init__(self, current_topic=None):
        self.current_topic = current_topic

def test_invalid_inputs():
    detector = AmbiguityDetector()
    u = DummyUnderstanding(None, 0.5, 0.5)
    res = detector.check_ambiguity(u, DummyState())
    assert res["is_ambiguous"] is True
    assert res["state"] == "invalid_input"
    assert res["clarification_needed"] == CLARIFICATION_MESSAGES["invalid_input"]

def test_boundary_known():
    detector = AmbiguityDetector(threshold=0.7, confidence_threshold=0.4)
    # Exactly on boundary -> not strictly > threshold
    u = DummyUnderstanding(ambiguity=0.7, context_dependency=0.1, confidence=0.4)
    res = detector.check_ambiguity(u, DummyState())
    assert res["is_ambiguous"] is False
    assert res["state"] == "known"

def test_missing_information():
    detector = AmbiguityDetector(threshold=0.7)
    # High ambiguity, no context
    u = DummyUnderstanding(ambiguity=0.8, context_dependency=0.1, confidence=0.9, topic=None)
    res = detector.check_ambiguity(u, DummyState())
    assert res["is_ambiguous"] is True
    assert res["state"] == "missing"
    assert "what you meant" in res["clarification_needed"]

def test_missing_information_with_unknown_topic():
    detector = AmbiguityDetector(threshold=0.7)
    # High ambiguity, topic is "unknown"
    u = DummyUnderstanding(ambiguity=0.8, context_dependency=0.1, confidence=0.9, topic="unknown")
    res = detector.check_ambiguity(u, DummyState())
    assert res["is_ambiguous"] is True
    assert res["state"] == "missing"
    assert "what you meant" in res["clarification_needed"]

def test_is_fallback():
    detector = AmbiguityDetector()
    u = DummyUnderstanding(ambiguity=0.0, context_dependency=0.0, confidence=0.0, is_fallback=True)
    res = detector.check_ambiguity(u, DummyState())
    # Fallback means semantic analysis failed (timeout/bad JSON) — we must NOT block
    # the user with a clarification request. Let the response proceed with best-effort context.
    assert res["is_ambiguous"] is False
    assert res["state"] == "inferred"
    assert res["clarification_needed"] is None

def test_inferred_with_low_confidence():
    detector = AmbiguityDetector(threshold=0.7, context_dependency_threshold=0.5, confidence_threshold=0.4)
    # High ambiguity, high context, but LOW confidence. 
    # Should fall through inferred branch and be treated as "missing" (because ambiguity is > 0.7).
    u = DummyUnderstanding(ambiguity=0.8, context_dependency=0.8, confidence=0.2, topic="budget")
    state = DummyState(current_topic="finance")
    res = detector.check_ambiguity(u, state)
    
    assert res["is_ambiguous"] is True
    assert res["state"] == "missing"

def test_inferred_with_high_confidence():
    detector = AmbiguityDetector(threshold=0.7, context_dependency_threshold=0.5, confidence_threshold=0.4)
    # High ambiguity, high context, HIGH confidence.
    u = DummyUnderstanding(ambiguity=0.8, context_dependency=0.8, confidence=0.9, topic="budget")
    state = DummyState(current_topic="finance")
    res = detector.check_ambiguity(u, state)
    
    assert res["is_ambiguous"] is False
    assert res["state"] == "inferred"

def test_uncertain():
    detector = AmbiguityDetector(threshold=0.7, confidence_threshold=0.4)
    # Low ambiguity, but also low confidence
    u = DummyUnderstanding(ambiguity=0.2, context_dependency=0.1, confidence=0.2)
    res = detector.check_ambiguity(u, DummyState())
    
    assert res["is_ambiguous"] is True
    assert res["state"] == "uncertain"
    assert res["clarification_needed"] == CLARIFICATION_MESSAGES["uncertain"]

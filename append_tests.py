tests = """
from backend.conversation_intelligence.nlg_policy import NLGPolicyEngine, ContextPolicyEngine
from backend.conversation_intelligence.continuity_detection import ContinuityDetectionEngine
from backend.conversation_intelligence.schemas import ContinuityRelationship, UserUnderstanding
from backend.conversation_intelligence.memory_pipeline import MemoryPipelineEngine
from backend.conversation_intelligence.mismatch_detector import MismatchDetectorEngine

def test_cq11_cq12_policies():
    nlg = NLGPolicyEngine().generate_policy()
    assert "NATURAL LANGUAGE GENERATION POLICY" in nlg
    assert "Avoid excessive formality" in nlg
    ctx = ContextPolicyEngine().generate_policy()
    assert "CONTEXTUAL RESPONSE POLICY" in ctx
    assert "Do not inject unrelated old context" in ctx

def test_cq13_cq14_continuity():
    engine = ContinuityDetectionEngine()
    result = engine.detect("Continue with the first thing", "t1", "task1")
    assert result.relationship == ContinuityRelationship.RETURN_PREVIOUS_TOPIC
    assert result.confidence < 0.8  # Needs clarification
    
    result2 = engine.detect("another topic", "t1", "task1")
    assert result2.relationship == ContinuityRelationship.TOPIC_SWITCH

def test_cq15_cq16_cq19_memory_pipeline():
    engine = MemoryPipelineEngine()
    # One turn correction (not persistent)
    res1 = engine.process_correction("that's not what i meant", is_explicit=False, repeat_count=1)
    assert res1 is None
    
    # Persistent due to explicit request
    res2 = engine.process_correction("that's wrong. always do it this way", is_explicit=True, repeat_count=1)
    assert res2 is not None
    assert res2.confidence == 0.9
    
    # Persistent due to repetition
    res3 = engine.process_correction("you misunderstood", is_explicit=False, repeat_count=3)
    assert res3 is not None
    assert res3.confidence == 0.8

def test_cq20_mismatch():
    engine = MismatchDetectorEngine()
    u = UserUnderstanding()
    u.desired_response_depth = "short"
    # Generated response is very long
    is_mismatch = engine.detect_mismatch(u, "a" * 600)
    assert is_mismatch is True
    
    u.explicit_current_instruction = "no code"
    is_mismatch2 = engine.detect_mismatch(u, "Here is code: ```python \\n print('hi') ```")
    assert is_mismatch2 is True
"""

with open('backend/tests/test_cq_baseline.py', 'a') as f:
    f.write(tests)

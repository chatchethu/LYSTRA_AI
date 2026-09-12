import os

def create_files():
    # CQ-11 & CQ-12
    nlg_policy = """\"\"\"
Phase CQ-11 — NATURAL LANGUAGE GENERATION POLICY
Phase CQ-12 — CONTEXTUAL RESPONSE POLICY
\"\"\"

class NLGPolicyEngine:
    def generate_policy(self) -> str:
        return (
            "NATURAL LANGUAGE GENERATION POLICY:\\n"
            "- Sound conversational.\\n"
            "- Use natural transitions.\\n"
            "- Respond directly.\\n"
            "- Avoid excessive formality, unnecessary headings, filler.\\n"
            "- Avoid repeated disclaimers, generic enthusiasm, forced empathy.\\n"
            "- Avoid repetitive closings.\\n"
            "Do not make every answer sound like a document.\\n"
        )

class ContextPolicyEngine:
    def generate_policy(self) -> str:
        return (
            "CONTEXTUAL RESPONSE POLICY:\\n"
            "- Prioritize current user request, current task, current topic.\\n"
            "- Prioritize relevant memory and relevant prior messages.\\n"
            "- Do not inject unrelated old context.\\n"
        )
"""
    with open('backend/conversation_intelligence/nlg_policy.py', 'w') as f:
        f.write(nlg_policy)

    # CQ-13 & CQ-14
    continuity_detection = """\"\"\"
Phase CQ-13 — CONVERSATION CONTINUITY
Phase CQ-14 — TOPIC RETURN INTELLIGENCE
\"\"\"
from backend.conversation_intelligence.schemas import ContinuityRelationship, ContinuityResult

class ContinuityDetectionEngine:
    def detect(self, message: str, active_topic_id: str, active_task_id: str) -> ContinuityResult:
        lower = message.lower()
        if "continue with the first thing" in lower or "go back to" in lower:
            # Topic return detected
            return ContinuityResult(
                relationship=ContinuityRelationship.RETURN_PREVIOUS_TOPIC,
                referenced_topic="previous_topic_id", # mocked resolution
                confidence=0.6 # low confidence requires clarification
            )
        elif "another topic" in lower:
            return ContinuityResult(relationship=ContinuityRelationship.TOPIC_SWITCH, confidence=0.9)
        elif "continue" in lower:
            return ContinuityResult(relationship=ContinuityRelationship.TASK_CONTINUATION, confidence=0.9)
        
        return ContinuityResult(relationship=ContinuityRelationship.SAME_TOPIC, confidence=0.8)
"""
    with open('backend/conversation_intelligence/continuity_detection.py', 'w') as f:
        f.write(continuity_detection)

    # CQ-15 & CQ-16 & CQ-19
    memory_pipeline = """\"\"\"
Phase CQ-15 — CORRECTION DETECTION
Phase CQ-16 — EXPLICIT USER CORRECTION LEARNING
Phase CQ-19 — USER CORRECTION → MEMORY PIPELINE
\"\"\"
from datetime import datetime
from typing import Optional
from backend.conversation_intelligence.schemas import LearnedPreference, PreferenceState

class MemoryPipelineEngine:
    def process_correction(self, message: str, is_explicit: bool = False, repeat_count: int = 1) -> Optional[LearnedPreference]:
        # Phase CQ-15
        lower = message.lower()
        correction_phrases = [
            "that's not what i meant", "you misunderstood", "no, i meant",
            "actually", "not that", "i meant", "that's wrong", "don't do that"
        ]
        
        is_correction = any(phrase in lower for phrase in correction_phrases)
        
        if not is_correction:
            return None
            
        # Phase CQ-16: Distinguish one-turn correction from persistent preference
        is_persistent = is_explicit or repeat_count >= 3
        
        if not is_persistent:
            return None
            
        # Phase CQ-19 Pipeline logic (Mocked deduplicate and conflict check)
        confidence = 0.9 if is_explicit else min(0.5 + (repeat_count * 0.1), 0.95)
        
        return LearnedPreference(
            preference=f"User prefers correction applied: {message}",
            confidence=confidence,
            source="user_correction",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            evidence_count=repeat_count,
            state=PreferenceState.ACTIVE
        )
"""
    with open('backend/conversation_intelligence/memory_pipeline.py', 'w') as f:
        f.write(memory_pipeline)

    # CQ-20
    mismatch_detector = """\"\"\"
Phase CQ-20 — RESPONSE MISMATCH DETECTION
\"\"\"
from backend.conversation_intelligence.schemas import UserUnderstanding, ResponseStrategy

class MismatchDetectorEngine:
    def detect_mismatch(self, understanding: UserUnderstanding, generated_response: str) -> bool:
        \"\"\"
        Compare understanding vs generated response.
        Detect wrong intent, need, topic, tone, depth, format, task.
        If mismatch, return True (revise).
        \"\"\"
        lower_response = generated_response.lower()
        
        # Simple heuristic: if understanding says short, but response is very long
        if understanding.desired_response_depth == "short" and len(generated_response) > 500:
            return True
            
        # If user explicitly said no code, but there is a code block
        if "no code" in understanding.explicit_current_instruction.lower() and "```" in lower_response:
            return True
            
        return False
"""
    with open('backend/conversation_intelligence/mismatch_detector.py', 'w') as f:
        f.write(mismatch_detector)

create_files()

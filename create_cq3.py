import os

def create_files():
    # CQ-21: User-Satisfaction Check
    satisfaction_check = """\"\"\"
Phase CQ-21 — USER-SATISFACTION CHECK
\"\"\"
from backend.conversation_intelligence.schemas import SatisfactionScores, UserUnderstanding

class UserSatisfactionEngine:
    def evaluate(self, understanding: UserUnderstanding, generated_response: str) -> SatisfactionScores:
        # Mock evaluation logic for phase validation
        scores = SatisfactionScores()
        lower = generated_response.lower()
        
        scores.understanding_score = 0.9
        scores.relevance_score = 0.9 if len(generated_response) > 10 else 0.4
        scores.naturalness_score = 0.8
        scores.depth_fit_score = 0.5 if len(generated_response) < 50 and understanding.desired_response_depth == "detailed" else 0.9
        scores.actionability_score = 0.8 if "plan" in lower or "step" in lower else 0.5
        scores.specificity_score = 0.8
        
        return scores
"""
    with open('backend/conversation_intelligence/satisfaction_check.py', 'w') as f:
        f.write(satisfaction_check)

    # CQ-22, CQ-23, CQ-24, CQ-25, CQ-28: Quality Filters
    quality_filters = """\"\"\"
Phase CQ-22 — GENERIC RESPONSE DETECTION
Phase CQ-23 — REPETITION CONTROL
Phase CQ-24 — OVER-EXPLANATION DETECTOR
Phase CQ-25 — UNDER-EXPLANATION DETECTOR
Phase CQ-28 — NATURAL FOLLOW-UP
\"\"\"
from typing import List

class ResponseQualityEngine:
    def detect_generic(self, text: str) -> bool:
        lower = text.lower()
        generics = [
            "that's a great question", "i completely understand", "believe in yourself",
            "here are some tips", "hope this helps", "let me know if you need anything else"
        ]
        return any(g in lower for g in generics)
        
    def detect_repetition(self, draft: str, recent_messages: List[str]) -> bool:
        # Simple repetition detection
        return draft in recent_messages
        
    def detect_over_explanation(self, draft: str) -> bool:
        # Detect unnecessary intros/summaries
        return "in conclusion" in draft.lower() or draft.count("\\n\\n") > 5
        
    def detect_under_explanation(self, request: str, draft: str) -> bool:
        lower_req = request.lower()
        if "explain" in lower_req or "architecture" in lower_req:
            if len(draft) < 100:
                return True
        return False
        
    def filter_response(self, draft: str) -> str:
        # Trim unnecessary generic follow-ups (CQ-28)
        return draft.replace("Let me know if you need anything else.", "Want me to turn this into a plan?")
"""
    with open('backend/conversation_intelligence/quality_filters.py', 'w') as f:
        f.write(quality_filters)

    # CQ-26, CQ-27: Ask-Or-Act Intelligence
    ask_or_act = """\"\"\"
Phase CQ-26 — ASK-OR-ACT INTELLIGENCE
Phase CQ-27 — QUESTION QUALITY
\"\"\"
from backend.conversation_intelligence.schemas import ClarificationDecision, UserUnderstanding

class AskOrActEngine:
    def determine(self, understanding: UserUnderstanding, missing_info: bool = False, high_risk: bool = False) -> ClarificationDecision:
        if understanding.ambiguity > 0.8 and missing_info and high_risk:
            return ClarificationDecision.ASK_QUESTION
        elif understanding.ambiguity > 0.5 and not high_risk:
            return ClarificationDecision.ANSWER_WITH_ASSUMPTION
        return ClarificationDecision.ANSWER
        
    def evaluate_question_quality(self, question: str, context: str) -> bool:
        \"\"\"
        Is it necessary? Can NOVA reasonably assume it?
        \"\"\"
        lower_q = question.lower()
        if "how are you" in lower_q:
            return False # Reject unnecessary questions
        if lower_q in context.lower():
            return False # Already answered
        return True
"""
    with open('backend/conversation_intelligence/ask_or_act.py', 'w') as f:
        f.write(ask_or_act)

    # CQ-29, CQ-30: Policy Gate
    policy_gate = """\"\"\"
Phase CQ-29 — STRICT POLICY GATE
Phase CQ-30 — PROTECTED INFORMATION CLASSIFICATION
\"\"\"
from backend.conversation_intelligence.schemas import ProtectedInfoCategory

class PolicyGateEngine:
    def check_policy(self, draft: str) -> bool:
        \"\"\"
        Return True if allowed, False if rejected due to policy violation.
        Checks privacy, security, system prompt leakage, credentials, etc.
        \"\"\"
        lower = draft.lower()
        forbidden = [
            "system prompt", "internal architecture", "api_key", "bearer token",
            "password", "secret", "user_private"
        ]
        if any(f in lower for f in forbidden):
            return False
        return True

    def classify_info(self, text: str) -> ProtectedInfoCategory:
        lower = text.lower()
        if "password" in lower or "api_key" in lower:
            return ProtectedInfoCategory.SECRET
        if "system internal" in lower or "backend architecture" in lower:
            return ProtectedInfoCategory.SYSTEM_INTERNAL
        return ProtectedInfoCategory.PUBLIC
"""
    with open('backend/conversation_intelligence/policy_gate.py', 'w') as f:
        f.write(policy_gate)

create_files()

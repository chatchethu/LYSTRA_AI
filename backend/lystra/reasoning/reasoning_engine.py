from backend.lystra.understanding.schemas import SemanticUnderstanding

class ReasoningEngine:
    def detect_correction(self, understanding: SemanticUnderstanding, previous_response: str) -> bool:
        """
        Phase 9: Conversation Repair
        Checks if the current intent represents a correction to a previous output.
        """
        is_correction_intent = understanding.intent.primary == "problem_solving" and understanding.intent.secondary == "correction"
        # We would also check semantic mismatches here.
        return is_correction_intent
        
    def adjust_strategy(self, understanding: SemanticUnderstanding, state):
        """Updates internal strategy without defending the previous wrong answer."""
        if self.detect_correction(understanding, "dummy"):
            state.active_goal = understanding.goal  # Pivot immediately
            # In a real impl, we would drop the conflicting memory context here.

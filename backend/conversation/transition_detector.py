from backend.intelligence.schemas import MessageUnderstanding
from backend.conversation.state import ConversationState

class TransitionDetector:
    """
    Phase 4: Detects whether the conversation has shifted.
    This prevents LYSTRA from rigidly sticking to one topic or stage.
    """
    
    @staticmethod
    def detect_transition(current_understanding: MessageUnderstanding, state: ConversationState) -> bool:
        """
        Returns True if a major conversational transition has occurred.
        """
        # If the stage changes (e.g., casual -> conflict, or sharing -> problem_solving)
        if state.conversation_stage != current_understanding.conversation_stage and state.conversation_stage != "casual":
            return True
            
        # If the target shifts dramatically (e.g. self -> LYSTRA -> third-party)
        # Note: We need a field in state to track active_target. Let's assume we update it.
        
        # If the emotion shifts intensely
        if abs(state.emotion_intensity - current_understanding.emotion_intensity) > 0.5:
            return True
            
        return False

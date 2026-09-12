from typing import Dict, List
from backend.lystra.context.conversation_state import ConversationState

class EntityExtractor:
    def resolve_references(self, message: str, state: ConversationState) -> Dict[str, str]:
        """
        Phase 22 & 23: Pronoun & Reference Resolution
        Resolves ambiguous terms (it, that, there, the above) to known entities.
        """
        ambiguous_terms = ["it", "that", "this", "same", "there", "the above", "the previous one"]
        resolved = {}
        
        message_lower = message.lower()
        if any(term in message_lower for term in ambiguous_terms):
            # In a real implementation, a fast LLM or SpaCy model would map this.
            # Mocking the resolution using the most recent important entity.
            if state.important_entities:
                last_entity_key = list(state.important_entities.keys())[-1]
                last_entity_val = state.important_entities[last_entity_key]
                resolved["that"] = last_entity_val
                resolved["it"] = last_entity_val
                
        return resolved

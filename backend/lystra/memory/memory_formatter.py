from typing import List
from .schemas import MemoryObject, MemoryType

class MemoryFormatter:
    """
    Phase 10 & 11: Natural Personalization and User Name Personalization.
    Translates raw memory objects into subtle prompt instructions for the LLM.
    """
    
    def _sanitize(self, text: str) -> str:
        """
        Fix #1: Sanitize memory content to prevent prompt injection 
        (e.g., breaking out of <USER_CONTEXT>).
        """
        # Ensure it's a string, strip tags, escape brackets, and cap length.
        sanitized = (
            str(text)
            .replace("<USER_CONTEXT>", "")
            .replace("</USER_CONTEXT>", "")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        return sanitized[:500]  # Length cap to prevent unbounded context growth

    def format_memories_for_prompt(self, memories: List[MemoryObject]) -> str:
        if not memories:
            return ""
            
        instructions = []
        instructions.append("<USER_CONTEXT>")
        instructions.append("Integrate these facts naturally without explicitly stating 'I remember'.")
        
        # Max item cap to prevent bloat (Fix #6 addition)
        cap_count = 0
        
        for m in memories:
            if cap_count >= 15:
                break
                
            # Safely fetch value and sanitize
            value = self._sanitize(getattr(m, "value", ""))
            
            # Fix #2: Use real type flag instead of fake key check
            if m.type == MemoryType.IDENTITY_NAME:
                # Phase 10: Special handling for names
                instructions.append(
                    f"- The user's preferred name is {value}. "
                    f"Use it occasionally for conversational warmth, but DO NOT use it in every response."
                )
            elif m.type == MemoryType.COMMUNICATION:
                # Phase 11: Natural Personalization
                instructions.append(f"- Communication preference: {value}")
            else:
                instructions.append(f"- Context: {value}")
            
            cap_count += 1
                
        instructions.append("</USER_CONTEXT>")
        
        return "\n".join(instructions)

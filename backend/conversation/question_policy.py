"""
Phase 14: Question Intelligence
Decides whether LYSTRA should ask a follow-up question.
"""
from typing import List, Dict

def should_ask_question(conversation_mode: str, history: List[Dict[str, str]], strategy_goals: List[str]) -> bool:
    """
    Returns True if a question is appropriate, False otherwise based on a question budget.
    """
    
    # If strategy explicitly calls for clarification, ask a question.
    if "CLARIFY" in strategy_goals:
        return True
        
    # If the user just asked a question, we shouldn't necessarily end with a question
    if history and history[-1]["role"] == "user":
        last_user_msg = history[-1]["content"].strip()
        if last_user_msg.endswith('?'):
            return False
          
    # QUESTION BUDGET: Check the last 5 assistant turns
    recent_assistant = [m["content"] for m in history[-10:] if m["role"] == "assistant"]
    questions_in_last_5 = sum(1 for m in recent_assistant[-5:] if '?' in m)
    
    # If we've asked 2 or more questions in the last 5 turns, BUDGET EXHAUSTED -> NO QUESTION
    if questions_in_last_5 >= 2:
        return False
        
    # Check if assistant asked a question in the very last turn to avoid interrogation mode
    if recent_assistant:
        last_asst_msg = recent_assistant[-1].strip()
        if '?' in last_asst_msg[-50:]:  # Question near the end
            return False  # Give them a break
            
    # In supportive/emotional modes, questions can feel intrusive if overused
    if conversation_mode in ("supportive", "reflective"):
        import random
        return random.random() < 0.2  # Only 20% chance to follow up with a question if budget allows
        
    # Default casual chat
    import random
    return random.random() < 0.4

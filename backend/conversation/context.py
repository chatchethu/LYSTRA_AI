"""
Phase 10: Conversation Memory / Context Manager
Combines recent turns, topic, facts, open threads, and conversation state into a single cohesive context block.
"""
from backend.conversation.state import ConversationState
from backend.conversation.open_threads import ThreadTracker

def build_context_block(
    state: ConversationState,
    thread_tracker: ThreadTracker,
    relevant_memory: str
) -> str:
    """Builds the comprehensive memory block for the LLM."""
    
    ctx = ""
    if relevant_memory:
        ctx += "IMPORTANT PREVIOUS FACTS:\n" + relevant_memory + "\n\n"
        
    unresolved = thread_tracker.get_unresolved_threads_context()
    if unresolved:
        ctx += unresolved + "\n"
        
    return ctx

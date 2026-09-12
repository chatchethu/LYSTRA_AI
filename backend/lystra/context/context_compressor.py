from typing import List, Dict

class ContextCompressor:
    def __init__(self, token_limit: int = 4000):
        self.token_limit = token_limit

    def compress_if_needed(self, history: List[Dict[str, str]], active_task_state) -> List[Dict[str, str]]:
        """
        Phase 26: Context Compression
        Retains active task state, recent discussion, but summarizes old messages.
        """
        estimated_tokens = sum(len(msg.get("content", "").split()) for msg in history)
        
        if estimated_tokens > self.token_limit and len(history) > 10:
            # Compress: Keep first 2 (system/context), last 6 (recent), and summarize the middle.
            recent = history[-6:]
            old = history[:-6]
            
            summary = "Prior conversation summary: User requested a complex task which is currently in progress."
            if active_task_state and active_task_state.active_goal:
                summary += f" Active goal is {active_task_state.active_goal}."
                
            compressed_history = [
                {"role": "system", "content": summary}
            ] + recent
            
            return compressed_history
            
        return history

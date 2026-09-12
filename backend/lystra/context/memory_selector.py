from typing import List

class MemorySelector:
    def should_use_memory(self, semantic_understanding) -> bool:
        """
        Phase 24 & 25: Memory Intelligence
        Decides if retrieved memory actually matters right now based on task dependency.
        """
        # If it's a simple clarification or casual chat with low context dependency, ignore memory.
        if semantic_understanding.context_dependency < 0.2 and semantic_understanding.intent.primary == "conversation":
            return False
            
        return True

    def filter_temporary_preferences(self, preferences: List[str]) -> List[str]:
        """
        Distinguish temporary conversational preference (e.g. 'be brief this time')
        from persistent user preference.
        """
        persistent = []
        for pref in preferences:
            if "this time" not in pref.lower() and "right now" not in pref.lower():
                persistent.append(pref)
        return persistent

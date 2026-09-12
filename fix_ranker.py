with open('backend/lystra/memory/memory_ranker.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_rank = '''    async def rank_for_context(self, user_request: str, candidates: List[MemoryObject]) -> List[MemoryObject]:
        """Phase 13: Semantic Memory Ranking"""
        if not candidates:
            return []'''

new_rank = '''    async def rank_for_context(self, user_request: str, candidates: List[MemoryObject]) -> List[MemoryObject]:
        """Phase 13: Semantic Memory Ranking"""
        if not candidates:
            return []
            
        # PERFORMANCE FIX: If the user has a small number of memories, skip the LLM ranking pass entirely.
        # It is astronomically faster to just inject 30 short strings into the final LLM prompt 
        # than to force a slow local model to execute a 30-second JSON evaluation loop.
        if len(candidates) < 50:
            return self.apply_relevance_threshold(candidates, threshold=0.1) # Pass almost everything through
'''

content = content.replace(old_rank, new_rank)

with open('backend/lystra/memory/memory_ranker.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Optimized MemoryRanker to skip LLM for small memory sets")

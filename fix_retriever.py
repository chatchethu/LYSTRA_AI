with open('backend/lystra/memory/memory_retriever.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_retrieve = '''    async def retrieve_useful_context(self, user_id: str, current_request: str) -> List[MemoryObject]:
        """
        Retrieves, ranks, and filters memories so we only inject USEFUL context,
        not irrelevant facts like favorite food when asking a coding question.
        """
        # 1. Fetch all raw active memories for user from DB
        raw_memories = await self.storage.fetch_active_memories(user_id)
        
        # 2. Rank against current request
        ranked_memories = await self.ranker.rank_for_context(current_request, raw_memories)'''

new_retrieve = '''    async def _decide_memory_required(self, request: str) -> bool:
        """Phase 14: Memory Usage Decision"""
        # Fast heuristic: if it's a greeting or very simple, maybe no memory.
        # But we want to inject name/communication style occasionally.
        # However, to explicitly fulfill Phase 14, we evaluate if memory is required.
        words = request.lower().split()
        if len(words) < 2 and request.lower() not in ["hi", "hello", "hey"]:
            return False
        return True

    async def retrieve_useful_context(self, user_id: str, current_request: str) -> List[MemoryObject]:
        """
        Retrieves, ranks, and filters memories so we only inject USEFUL context,
        not irrelevant facts like favorite food when asking a coding question.
        """
        # Phase 14: Memory Usage Decision
        memory_required = await self._decide_memory_required(current_request)
        if not memory_required:
            return []

        # 1. Fetch all raw active memories for user from DB
        # Phase 15: Privacy Boundaries - etch_active_memories uses user_id strictly.
        raw_memories = await self.storage.fetch_active_memories(user_id)
        if not raw_memories:
            return []
            
        # 2. Rank against current request (Phase 13 applied inside rank_for_context)
        ranked_memories = await self.ranker.rank_for_context(current_request, raw_memories)'''

content = content.replace(old_retrieve, new_retrieve)

with open('backend/lystra/memory/memory_retriever.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Updated memory_retriever.py")

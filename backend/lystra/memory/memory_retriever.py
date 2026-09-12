from typing import List
from .schemas import MemoryObject
from .memory_ranker import MemoryRanker

class MemoryRetriever:
    """
    Phase 12: Memory Retrieval execution layer.
    """
    def __init__(self, llm_gateway, storage_backend):
        self.ranker = MemoryRanker(llm_gateway)
        self.storage = storage_backend

    async def _decide_memory_required(self, request: str) -> bool:
        """Phase 14: Memory Usage Decision"""
        # Fast heuristic: if it's a greeting or very simple, maybe no memory.
        # Fix #5: Corrected the inverted logic. Greetings should skip memory read.
        request_lower = request.lower()
        if request_lower in ["hi", "hello", "hey"]:
            return False
            
        words = request_lower.split()
        if len(words) < 2:
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
        # Phase 15: Privacy Boundaries - fetch_active_memories uses user_id strictly.
        raw_memories = await self.storage.fetch_active_memories(user_id)
        if not raw_memories:
            return []
            
        # 2. Rank against current request (Phase 13 applied inside rank_for_context)
        ranked_memories = await self.ranker.rank_for_context(current_request, raw_memories)
        
        # 3. Update last_used_at for lifecycle tracking (Phase 8)
        # Fix #4: Batch the last_used_at updates instead of looping and calling update_memory.
        if ranked_memories:
            # Gather memory IDs and call touch_last_used on the storage backend
            memory_ids = [m.id for m in ranked_memories if m.id]
            if memory_ids:
                await self.storage.touch_last_used(memory_ids)
            
        return ranked_memories

from typing import List
from .schemas import MemoryObject
from .memory_ranker import MemoryRanker

import structlog

logger = structlog.get_logger(__name__)

class MemoryRetriever:
    """
    Phase 12: Memory Retrieval execution layer.
    """
    def __init__(self, llm_gateway, storage_backend):
        self.llm = llm_gateway
        self.ranker = MemoryRanker(llm_gateway)
        self.storage = storage_backend

    async def _decide_memory_required(self, request: str, understanding=None) -> bool:
        """Phase 14: Memory Usage Decision
        Lystra must make a decision: memory_required = true/false
        If false: do not inject unnecessary personal information.
        If true: retrieve only the minimum necessary memory. This prevents over-personalization.
        """
        if understanding:
            # If semantic analyzer says this is just a generic greeting or very low context dependency
            # we explicitly skip memory to prevent over-personalization
            primary_intent = getattr(understanding.intent, "primary", "")
            if hasattr(primary_intent, "value"):
                primary_intent = primary_intent.value
            if primary_intent == "conversation" and understanding.context_dependency < 0.2:
                # Still check if they are asking something personal implicitly
                request_lower = request.lower()
                if "my" not in request_lower and "i " not in request_lower and "me " not in request_lower:
                    return False

        request_lower = request.lower()
        if request_lower in ["hi", "hello", "hey"]:
            return False
            
        words = request_lower.split()
        if len(words) < 2:
            return False
            
        return True

    async def retrieve_useful_context(self, user_id: str, current_request: str, understanding=None) -> List[MemoryObject]:
        """
        Retrieves, ranks, and filters memories so we only inject USEFUL context,
        not irrelevant facts like favorite food when asking a coding question.
        """
        # Phase 14: Memory Usage Decision
        memory_required = await self._decide_memory_required(current_request, understanding)
        if not memory_required:
            return []

        # RAG Vector Search Pipeline
        try:
            query_embedding = await self.llm.embed(current_request)
            # Fetch top 20 most semantically similar memories
            raw_memories = await self.storage.search_by_embedding(user_id, query_embedding, limit=20)
            
            # Fallback to fetching all active if vector search yields nothing 
            # (e.g. for legacy memories without embeddings yet)
            if not raw_memories:
                raw_memories = await self.storage.fetch_active_memories(user_id)
        except Exception as e:
            logger.warning("rag_search_failed_falling_back", error=str(e))
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

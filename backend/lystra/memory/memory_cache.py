import json
from typing import List
from .schemas import MemoryObject, MemoryType, MemoryStatus, MemorySource
import structlog

logger = structlog.get_logger("lystra.memory_cache")

class SecureMemoryCache:
    """
    Phase 38: Memory Caching Security
    Enforces strict identity boundaries in cache keys to prevent cross-user leakage.
    Format: memory:{user_id}:active
    """
    def __init__(self, redis_client=None):
        self.redis = redis_client

    def _get_user_key(self, user_id: str) -> str:
        return f"memory:{user_id}:active"

    async def get_memories(self, user_id: str) -> List[MemoryObject]:
        if not self.redis: return []
        key = self._get_user_key(user_id)
        try:
            cached = await self.redis.get(key)
            if cached:
                data = json.loads(cached)
                # Reconstruct MemoryObjects
                return [MemoryObject(**m) for m in data]
        except Exception as e:
            logger.error("memory_cache_read_error", error=str(e))
        return []

    async def set_memories(self, user_id: str, memories: List[MemoryObject], ttl: int = 3600):
        if not self.redis: return
        key = self._get_user_key(user_id)
        try:
            data = [m.model_dump(mode='json') for m in memories]
            await self.redis.set(key, json.dumps(data), ex=ttl)
        except Exception as e:
            logger.error("memory_cache_write_error", error=str(e))

    async def invalidate(self, user_id: str):
        if not self.redis: return
        key = self._get_user_key(user_id)
        try:
            await self.redis.delete(key)
        except Exception as e:
            logger.error("memory_cache_invalidate_error", error=str(e))

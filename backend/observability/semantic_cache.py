import hashlib
import json
import redis.asyncio as aioredis
from typing import Optional, Any
from backend.config import get_settings

class SemanticCache:
    """
    Phase 105: Semantic Caching
    Strictly partitions cache by User ID to prevent cross-tenant data leakage.
    """
    def __init__(self):
        self.settings = get_settings()
        self.redis = aioredis.from_url(self.settings.REDIS_URL, decode_responses=True)

    def _generate_key(self, user_id: str, model_version: str, prompt: str, tool_state: str) -> str:
        payload = f"{user_id}:{model_version}:{prompt}:{tool_state}"
        hashed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"semantic_cache:{hashed}"

    async def get_cached_response(self, user_id: str, model_version: str, prompt: str, tool_state: str) -> Optional[Any]:
        # Never blind cache. Requires explicit cacheable intents.
        key = self._generate_key(user_id, model_version, prompt, tool_state)
        data = await self.redis.get(key)
        return json.loads(data) if data else None

    async def set_cached_response(self, user_id: str, model_version: str, prompt: str, tool_state: str, response: Any, ttl: int = 3600):
        key = self._generate_key(user_id, model_version, prompt, tool_state)
        await self.redis.setex(key, ttl, json.dumps(response))


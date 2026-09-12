with open('backend/tools/web/web_search.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Fix 1: RedisCircuitBreaker Try/Except
old_cb = '''class RedisCircuitBreaker:
    def __init__(self, redis, name, failure_threshold: int = 3, recovery_timeout: float = 60.0):
        self.redis = redis
        self.key = f"circuit:{name}"
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

    async def record_failure(self):
        pipe = self.redis.pipeline()
        pipe.incr(self.key)
        pipe.expire(self.key, int(self.recovery_timeout))
        await pipe.execute()

    async def record_success(self):
        await self.redis.delete(self.key)

    async def is_open(self) -> bool:
        count = await self.redis.get(self.key)
        return int(count or 0) >= self.failure_threshold'''

new_cb = '''class RedisCircuitBreaker:
    def __init__(self, redis, name, failure_threshold: int = 3, recovery_timeout: float = 60.0):
        self.redis = redis
        self.key = f"circuit:{name}"
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

    async def record_failure(self):
        try:
            pipe = self.redis.pipeline()
            pipe.incr(self.key)
            pipe.expire(self.key, int(self.recovery_timeout))
            await pipe.execute()
        except Exception:
            pass

    async def record_success(self):
        try:
            await self.redis.delete(self.key)
        except Exception:
            pass

    async def is_open(self) -> bool:
        try:
            count = await self.redis.get(self.key)
            return int(count or 0) >= self.failure_threshold
        except Exception:
            return False'''

content = content.replace(old_cb, new_cb)

# Fix 2: _check_rate_limit Try/Except
old_rl = '''    async def _check_rate_limit(self, user_id: str) -> bool:
        key = f"rate_limit:web_search:{user_id}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 3600)
        return count <= self.settings.WEB_SEARCH_RATE_LIMIT_PER_HOUR'''

new_rl = '''    async def _check_rate_limit(self, user_id: str) -> bool:
        key = f"rate_limit:web_search:{user_id}"
        try:
            count = await self.redis.incr(key)
            if count == 1:
                await self.redis.expire(key, 3600)
            return count <= self.settings.WEB_SEARCH_RATE_LIMIT_PER_HOUR
        except Exception:
            return True # fail open'''

content = content.replace(old_rl, new_rl)

# Fix 3: Clamp max_results & unused import
old_exec_start = '''    async def execute(self, user_id, task_id=None, conversation_id=None, request_id=None, query: str = "", queries: List[str] = None, max_results: int = 5, llm=None, model_router=None, freshness_required: bool = False, budget=None, **kwargs) -> ToolResult:
        start_time = time.time()'''

new_exec_start = '''    async def execute(self, user_id, task_id=None, conversation_id=None, request_id=None, query: str = "", queries: List[str] = None, max_results: int = 5, llm=None, model_router=None, freshness_required: bool = False, budget=None, **kwargs) -> ToolResult:
        start_time = time.time()
        max_results = max(1, min(max_results, 10))'''

content = content.replace(old_exec_start, new_exec_start)

with open('backend/tools/web/web_search.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("web_search.py partial patch 1 applied")

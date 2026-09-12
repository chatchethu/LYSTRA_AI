from typing import Callable
from fastapi import Request
import redis.asyncio as redis
from backend.config import get_settings
from backend.api.errors import RateLimitError

settings = get_settings()

# Initialize async redis pool
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class RateLimiter:
    def __init__(self, limit: int, window: int, key_func: Callable[[Request], str]):
        self.limit = limit
        self.window = window
        self.key_func = key_func

    async def __call__(self, request: Request):
        key = self.key_func(request)
        if not key:
            return  # Skip if key cannot be determined
        
        redis_key = f"rate_limit:{key}"
        
        try:
            current_count = await redis_client.get(redis_key)
            if current_count and int(current_count) >= self.limit:
                raise RateLimitError(detail=f"Rate limit exceeded. Limit: {self.limit} per {self.window}s.")
            
            pipeline = redis_client.pipeline()
            pipeline.incr(redis_key)
            # Only set expire on first increment
            if not current_count:
                pipeline.expire(redis_key, self.window)
            await pipeline.execute()
        except redis.ConnectionError:
            pass # Skip rate limiting if redis is unavailable (e.g. tests)

def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"

def get_anon_session_id(request: Request) -> str:
    session_id = request.cookies.get("session_id")
    return session_id if session_id else get_client_ip(request)

def get_user_id(request: Request) -> str:
    # Assuming user ID is added to state by auth middleware
    user = getattr(request.state, "user", None)
    return str(user.id) if user else get_anon_session_id(request)

# Define common rate limiters
# General IP-based rate limiting for endpoints
ip_rate_limit = RateLimiter(limit=100, window=60, key_func=lambda r: f"ip:{get_client_ip(r)}:{r.url.path}")

# Anonymous session rate limiting
anon_session_limit = RateLimiter(limit=50, window=60, key_func=lambda r: f"anon:{get_anon_session_id(r)}:{r.url.path}")

# User-based rate limiting
user_rate_limit = RateLimiter(limit=200, window=60, key_func=lambda r: f"user:{get_user_id(r)}:{r.url.path}")

# Specific limits for expensive operations
model_usage_limit = RateLimiter(limit=10, window=60, key_func=lambda r: f"model:{get_user_id(r)}")
file_upload_limit = RateLimiter(limit=5, window=60, key_func=lambda r: f"upload:{get_user_id(r)}")
tool_usage_limit = RateLimiter(limit=20, window=60, key_func=lambda r: f"tool:{get_user_id(r)}")
task_creation_limit = RateLimiter(limit=10, window=60, key_func=lambda r: f"task:{get_user_id(r)}")

# Helper dependency to combine multiple limiters
class MultiRateLimit:
    def __init__(self, *limiters: RateLimiter):
        self.limiters = limiters
        
    async def __call__(self, request: Request):
        for limiter in self.limiters:
            await limiter(request)

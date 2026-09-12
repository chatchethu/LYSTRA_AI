import redis.asyncio as redis
from backend.config import get_settings

settings = get_settings()

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

async def block_token_jti(jti: str, expires_in: int):
    if expires_in > 0:
        try:
            await redis_client.setex(f"blocklist:{jti}", expires_in, "true")
        except redis.ConnectionError:
            pass

async def is_jti_blocked(jti: str) -> bool:
    if not jti:
        return False
    try:
        return await redis_client.exists(f"blocklist:{jti}") > 0
    except redis.ConnectionError:
        return False

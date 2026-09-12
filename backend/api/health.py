from fastapi import APIRouter, Response, status
import httpx
from sqlalchemy import text
import redis.asyncio as aioredis
from backend.db.session import AsyncSessionLocal
from backend.config import get_settings

router = APIRouter(tags=["health"])

@router.get("/live")
async def liveness_probe():
    """Phase 77: Basic liveness check. Proves the event loop is responsive."""
    return {"status": "alive"}

@router.get("/ready")
async def readiness_probe(response: Response):
    """Phase 77: Deep readiness check. Proves dependencies are available."""
    settings = get_settings()
    health_status = {
        "status": "ready",
        "database": "unknown",
        "redis": "unknown",
        "ollama": "unknown"
    }
    
    is_ready = True
    
    # 1. Check PostgreSQL
    try:
        async with AsyncSessionLocal() as db:
            await db.execute(text("SELECT 1"))
            health_status["database"] = "ok"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        is_ready = False

    # 2. Check Redis
    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await r.ping()
        health_status["redis"] = "ok"
        await r.aclose()
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        is_ready = False

    # 3. Check Ollama
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/version")
            if res.status_code == 200:
                health_status["ollama"] = "ok"
            else:
                health_status["ollama"] = f"error: status {res.status_code}"
                is_ready = False
    except Exception as e:
        health_status["ollama"] = f"error: {str(e)}"
        is_ready = False
        
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        health_status["status"] = "not_ready"
        
    return health_status


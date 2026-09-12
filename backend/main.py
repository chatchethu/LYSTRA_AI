import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import structlog

from backend.config import get_settings
from backend.db.session import init_db
from backend.llm.ollama_provider import OllamaProvider
from backend.llm.gateway import LLMGateway
from backend.api import messages, auth, conversations, memories, models, settings, health, privacy, speech

settings_conf = get_settings()
logger = structlog.get_logger()

# Optional routers — gracefully skip if dependencies are missing
try:
    from backend.api import files as files_router
    _has_files = True
except Exception as e:
    logger.warning("files_router_unavailable", error=str(e))
    _has_files = False

try:
    from backend.api import tools as tools_router
    _has_tools = True
except Exception as e:
    logger.warning("tools_router_unavailable", error=str(e))
    _has_tools = False



try:
    from backend.api import admin as admin_router
    _has_admin = True
except Exception as e:
    logger.warning("admin_router_unavailable", error=str(e))
    _has_admin = False

# Global LLM Gateway
llm_gateway = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up LYSTRA AI backend")

    # Initialize DB (non-fatal — app can still serve LLM chat without DB)
    try:
        logger.info("Initializing database")
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning("database_init_skipped", error=str(e))

    # Setup LLM Gateway
    logger.info("Setting up LLM gateway with Ollama")
    global llm_gateway
    ollama_provider = OllamaProvider()
    llm_gateway = LLMGateway(ollama_provider)

    # Verify Ollama is reachable and models are available
    try:
        if await ollama_provider.health_check():
            logger.info("Ollama connected and healthy")
            from backend.events.publisher import start_outbox_publisher
            start_outbox_publisher()
            logger.info("Started outbox publisher")
            # Phase 10 - Model Availability Check
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings_conf.OLLAMA_BASE_URL}/api/tags")
                if resp.status_code == 200:
                    available = [m["name"] for m in resp.json().get("models", [])]
                    required_models = [
                        settings_conf.OLLAMA_CHAT_MODEL,
                        settings_conf.OLLAMA_CODE_MODEL
                    ]
                    for model in required_models:
                        if model not in available:
                            logger.error("Configured model unavailable", model=model)
                        else:
                            logger.info("Model available", model=model)
        else:
            logger.warning("Ollama health check failed — ensure Ollama is running on port 11434")
    except Exception as e:
        logger.warning("Ollama not reachable", error=str(e))

    yield

    # Shutdown
    logger.info("Shutting down LYSTRA AI backend")

app = FastAPI(
    title="LYSTRA AI Agent",
    description="Production-ready LYSTRA AI agent with memory, tools, and planning",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_conf.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Secure Headers Middleware
@app.middleware("http")
async def secure_headers_middleware(request: Request, call_next):
    # CSRF protection for mutating requests (Basic check)
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        origin = request.headers.get("origin")
        if origin and origin not in settings_conf.CORS_ORIGINS:
            return JSONResponse(status_code=403, content={"detail": "CSRF verification failed."})

    response = await call_next(request)
    
    # Security Headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response

# Request ID Middleware
@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(request_id=request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    structlog.contextvars.clear_contextvars()
    return response

# Global Rate Limiting Middleware
from backend.api.rate_limit import ip_rate_limit, RateLimitError

@app.middleware("http")
async def global_rate_limit_middleware(request: Request, call_next):
    # Skip rate limiting for static/docs/health
    if request.url.path.startswith(("/docs", "/openapi.json", "/live", "/ready")):
        return await call_next(request)
        
    try:
        await ip_rate_limit(request)
    except RateLimitError as e:
        return JSONResponse(status_code=e.status_code, content=e.detail, headers=e.headers)
        
    return await call_next(request)


# Exception Handlers
from backend.api.errors import LystraError

@app.exception_handler(LystraError)
async def lystra_error_handler(request: Request, exc: LystraError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
        headers=exc.headers
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error("unhandled_exception", error=str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Routers — core
app.include_router(messages.router)
app.include_router(auth.router)
app.include_router(conversations.router)
app.include_router(memories.router)
app.include_router(models.router)
from backend.api import settings as api_settings
app.include_router(api_settings.router)
app.include_router(privacy.router)
app.include_router(speech.router)



# Routers — optional (skip if dependencies missing)
if _has_files:
    app.include_router(files_router.router)
if _has_tools:
    app.include_router(tools_router.router)

if _has_admin:
    app.include_router(admin_router.router)

app.include_router(health.router)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


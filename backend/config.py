from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LYSTRA AI"
    APP_ENV: str = "development"
    SECRET_KEY: str
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    # AWS S3 Storage
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = "lystra-ai-bucket"

    # Ollama
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_CHAT_MODEL: str = "llama3.2:latest"
    FALLBACK_CHAT_MODEL: str = "qwen2.5:coder"
    OLLAMA_CODE_MODEL: str = "qwen2.5:3b"
    OLLAMA_VISION_MODEL: str = "qwen2.5vl:3b"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"
    SEMANTIC_ANALYSIS_TIMEOUT_S: float = 500.0
    # LLM gateway per-call timeout and total deadline (used by lystra/llm_gateway.py)
    LLM_CALL_TIMEOUT_SECONDS: float = 500.0
    LLM_TOTAL_DEADLINE_SECONDS: float = 500.0
    # Tool routing LLM call — set high enough for local Llama (18-30s observed in logs)
    TOOL_ROUTING_MODEL: str = "llama3.2:latest"
    TOOL_ROUTING_TIMEOUT_S: float = 500.0

    # Ambiguity Detection Thresholds
    AMBIGUITY_THRESHOLD: float = 0.7
    AMBIGUITY_CONTEXT_THRESHOLD: float = 0.5
    AMBIGUITY_CONFIDENCE_THRESHOLD: float = 0.4

    # Memory classification LLM call — was hardcoded at 10s which always timed out on local Llama
    MEMORY_CLASSIFICATION_TIMEOUT_S: float = 500.0

    # Speech to text
    SARVAM_API_KEY: Optional[str] = None
    SARVAM_API_KEYS: list[str] = [] # Supports rotation
    SARVAM_STT_MODEL: str = "saaras:v3"
    SARVAM_STT_MODE: str = "transcribe"
    SARVAM_STT_URL: str = "https://api.sarvam.ai/speech-to-text"

    # Security
    FIRECRAWL_BASE_URL: str = "https://api.firecrawl.dev/v1/search"
    FIRECRAWL_API_KEY: Optional[str] = None
    
    # Web Search Configuration
    WEB_SEARCH_RATE_LIMIT_PER_HOUR: int = 50
    WEB_SEARCH_CACHE_TTL: int = 3600
    WEB_SEARCH_MAX_QUERIES: int = 3
    WEB_SEARCH_OUTER_TIMEOUT: float = 500.0
    WEB_SEARCH_FETCH_TIMEOUT: float = 60.0
    WEB_SEARCH_EXTRACTION_TIMEOUT: float = 500.0
    
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days — avoids session expiry during development
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Cors
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50

    # Workers
    CELERY_WORKERS: int = 4

    # Post-Production Configuration
    SHADOW_MODE: bool = False  # If True, blocks dangerous tools but tracks intent

    # Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    
    if settings.APP_ENV == "production":
        if settings.DEBUG:
            raise ValueError("APP_ENV is production but DEBUG is True. Refusing to start.")
            
    return settings


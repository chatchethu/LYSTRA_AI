from typing import AsyncGenerator
import structlog
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

from backend.config import get_settings

logger = structlog.get_logger(__name__)
settings = get_settings()

# We use the default connection pool for better throughput, rather than NullPool.
# Pre-ping prevents stale connection errors.
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT,    # seconds to wait for a free connection
    pool_pre_ping=True,
    pool_recycle=settings.DATABASE_POOL_RECYCLE,    # recycle connections before they go stale
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Automatically commit on success so writes persist without manual commits
            # in every route handler.
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def init_db() -> None:
    try:
        async with engine.begin() as conn:
            # Create vector extension first so Memory table can be created
            await conn.execute(text('CREATE EXTENSION IF NOT EXISTS vector'))
            # Production schema management is handled by Alembic migrations.
    except Exception as e:
        logger.exception("Failed to ensure pgvector extension exists — check DB role privileges", error=str(e))
        raise

async def close_db() -> None:
    await engine.dispose()

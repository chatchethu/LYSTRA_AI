import uuid
import asyncio
import structlog
from typing import List, Optional
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import pool

from .schemas import MemoryObject, MemoryType, MemoryStatus
from .memory_extractor import MemoryExtractor
from .memory_updater import MemoryUpdater
from .memory_retriever import MemoryRetriever
from .memory_formatter import MemoryFormatter

from backend.config import get_settings
from backend.crud.memory import memory as crud_memory
from backend.db.models.memory import Memory

logger = structlog.get_logger(__name__)

class DBMemoryStorage:
    """
    All DB sessions in this class use a fresh NullPool engine per call.

    Why NOT AsyncSessionLocal (the global engine)?
    ------------------------------------------------
    Celery workers run each task via asyncio.run(), which creates a brand-new
    event loop for every task. The global engine uses a connection pool whose
    connections are bound to the event loop that was active at import time
    (or the first time the pool was used). When a new asyncio.run() call
    starts, those pooled connections are stale and throw:
      - 'NoneType' object has no attribute 'send'
      - RuntimeError: Event loop is closed  (on pool teardown)

    NullPool creates and closes a real TCP connection per session — no
    pooling, no loop-affinity — which works correctly in every asyncio.run()
    context.
    """

    _loop_engines = {}

    @asynccontextmanager
    async def _session(self):
        """
        Yields an AsyncSession using an engine that is securely bound to the 
        CURRENT asyncio event loop. This avoids the Celery "Event loop is closed" 
        crash, while utilizing a QueuePool to prevent TCP port exhaustion (WinError 64) 
        caused by NullPool rapidly opening/closing sockets.
        """
        loop = asyncio.get_running_loop()
        if loop not in self._loop_engines:
            settings = get_settings()
            # Use a small QueuePool per loop
            engine = create_async_engine(
                settings.DATABASE_URL, 
                pool_size=5, 
                pool_pre_ping=True
            )
            self._loop_engines[loop] = engine
            
        engine = self._loop_engines[loop]
        LocalSession = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        try:
            async with LocalSession() as session:
                yield session
        except Exception:
            raise

    async def fetch_active_memories(self, user_id):
        async with self._session() as db:
            now = datetime.now(timezone.utc)
            # Fix #6: SQL filtering instead of Python loop filtering
            stmt = select(Memory).where(
                Memory.user_id == uuid.UUID(str(user_id)),
                Memory.status.in_(["active", "validated", "updated"]),
                or_(Memory.expires_at.is_(None), Memory.expires_at > now)
            )
            result = await db.execute(stmt)
            mems = result.scalars().all()

            # Map legacy memory_type values that were stored under an older enum
            # to the closest current MemoryType value, so old DB rows don't crash.
            LEGACY_TYPE_MAP = {
                "statement":    MemoryType.CONTEXT.value,
                "fact":         MemoryType.CONTEXT.value,
                "task":         MemoryType.RECURRING_TASK.value,
                "emotion":      MemoryType.CONTEXT.value,
                "constraint":   MemoryType.PREFERENCE.value,
                "decision":     MemoryType.CONTEXT.value,
                "communication": MemoryType.COMMUNICATION.value,
            }

            objs = []
            for m in mems:
                try:
                    raw_type = m.memory_type or ""
                    # Remap legacy value → current enum value if needed
                    remapped_type = LEGACY_TYPE_MAP.get(raw_type, raw_type)
                    mem_type = MemoryType(remapped_type) if remapped_type else MemoryType.PREFERENCE
                    obj = MemoryObject(
                        id=str(m.id),
                        user_id=str(m.user_id),
                        type=mem_type,
                        key=m.canonical_key or m.content[:50],  # Fix: Use real canonical_key or fallback
                        value=m.content,
                        confidence=m.confidence,
                        importance=m.importance,
                        source="user_explicit",
                        status="active"
                    )
                    objs.append(obj)
                except Exception as e:
                    # Fix #7: Real logging instead of silent pass
                    logger.warning("memory_conversion_failed", memory_id=str(m.id), error=str(e))
            return objs

    async def _audit(self, db, user_id, action, memory_id=None, details=None):
        """Phase 39: Audit Logging"""
        from backend.db.models.audit_log import AuditLog
        try:
            log = AuditLog(
                user_id=uuid.UUID(str(user_id)),
                action=action,
                resource_type="memory",
                resource_id=str(memory_id) if memory_id else None,
                # Fix #7: Dynamic details parameter
                details=details or {"status": "success"} 
            )
            db.add(log)
        except Exception as e:
            # Fix #7: Do not silently swallow audit failures
            logger.error("audit_log_failed", user_id=str(user_id), action=action, error=str(e))

    async def update_memory(self, memory: MemoryObject):
        # Fix #1: Actually UPDATE the memory instead of creating a duplicate
        if not memory.id:
            logger.error("update_memory_called_without_id", user_id=str(memory.user_id))
            return
            
        async with self._session() as db:
            content_str = str(memory.value)[:10000] # Length cap
            update_data = {
                "content": content_str,
                "importance": memory.importance,
                "confidence": memory.confidence,
                "status": memory.status,
                "canonical_key": memory.key,
                "memory_type": memory.type.value if hasattr(memory.type, "value") else memory.type
            }
            await crud_memory.update_memory_row(db, uuid.UUID(str(memory.id)), update_data)
            await self._audit(db, memory.user_id, "memory_updated", memory.id)
            await db.commit()
            
    async def deactivate_memory(self, memory: MemoryObject):
        # Fix #2: Actually deactivate the memory in DB
        if not memory.id:
            logger.warning("deactivate_memory_called_without_id", user_id=str(memory.user_id))
            return
            
        async with self._session() as db:
            await crud_memory.update_status(db, uuid.UUID(str(memory.id)), MemoryStatus.DELETED.value)
            await self._audit(db, memory.user_id, "memory_deleted", memory.id)
            await db.commit()

    async def add_memory(self, memory: MemoryObject):
        content_str = str(memory.value)[:10000] # Fix: Hard cap length
        async with self._session() as db:
            from backend.schemas.memory import MemoryCreate
            obj_in = MemoryCreate(
                user_id=uuid.UUID(str(memory.user_id)),
                memory_type=memory.type.value if hasattr(memory.type, "value") else memory.type,
                content=content_str,
                importance=memory.importance,
                confidence=memory.confidence,
                canonical_key=memory.key
            )
            mem = await crud_memory.create(db, obj_in=obj_in)
            await self._audit(db, memory.user_id, "memory_created", mem.id)
            await db.commit()
            
    async def touch_last_used(self, memory_ids: List[str]):
        # Fix #4: Batch last_used_at updates
        if not memory_ids:
            return
        async with self._session() as db:
            now = datetime.now(timezone.utc)
            uuids = [uuid.UUID(m_id) for m_id in memory_ids]
            await crud_memory.touch_last_used(db, uuids, now)
            await db.commit()


class MemoryManager:
    """
    Central orchestrator for the Lystra Memory Subsystem.
    Hooks into the ExecutionManager.
    """
    def __init__(self, llm_gateway):
        self.extractor = MemoryExtractor(llm_gateway)
        self.updater = MemoryUpdater()
        self.storage = DBMemoryStorage()
        self.retriever = MemoryRetriever(llm_gateway, self.storage)
        self.formatter = MemoryFormatter()

    async def process_user_message(self, user_id: str, message: str, context_history: List[str], intent: str = "conversation"):
        """
        Phase 1-9 & 20-23: Analyzes incoming messages to extract, deduplicate, and update memories.
        """
        # Phase 20: Memory Extraction Timing
        if intent in ["greeting", "farewell", "acknowledgment"]:
            return

        # Phase 27: "Forget This" Semantics
        # Improve "forget" intent check
        msg_lower = message.lower()
        if "forget" in msg_lower.split() or "do not remember" in msg_lower or "delete that" in msg_lower:
            existing_memories = await self.storage.fetch_active_memories(user_id)
            
            # Use real MemoryObject
            candidate = MemoryObject(
                user_id=user_id,
                type=MemoryType.PREFERENCE,
                key="forget_candidate",
                value=message,
                status=MemoryStatus.ACTIVE,
                confidence=1.0,
                importance=0.8,
                source="user_explicit"
            )
            
            conflict = await self.updater.find_semantic_conflict(
                candidate=candidate,
                existing=existing_memories, 
                llm=self.extractor.llm
            )
            if conflict:
                # Fix #3: Call deactivate_memory instead of update_memory
                await self.storage.deactivate_memory(conflict)
                return

        # Fetch memories once and reuse (Fix redundant fetch)
        existing_memories = await self.storage.fetch_active_memories(user_id)

        candidate = await self.extractor.extract_candidate_memory(user_id, message, context_history)
        if candidate:
            conflict = await self.updater.find_semantic_conflict(candidate, existing_memories, self.extractor.llm)
            
            if conflict:
                resolved = self.updater.resolve_conflict(conflict, candidate)
                # Ensure the resolved memory retains the conflict ID so it actually updates
                if not resolved.id:
                    resolved.id = conflict.id
                await self.storage.update_memory(resolved)
            else:
                await self.storage.add_memory(candidate)
                
            # Phase 23: Memory Consolidation
            # It's safe to await here because process_user_message is ALREADY running
            # inside an execution_manager background task, so it doesn't block the stream.
            try:
                await self.updater.consolidate_memories(existing_memories, self.storage, self.extractor.llm)
            except Exception as e:
                logger.error("memory_consolidation_failed", error=str(e))

    async def get_contextual_prompt_injection(
        self, user_id: str, current_request: str, verified_name: str = ""
    ) -> str:
        """
        Phase 10-12: Retrieves relevant memories and formats them for natural personalization.

        verified_name: if set (from DB account record), any IDENTITY_NAME / IDENTITY memories
        are stripped before injection — the verified name is already in the [VERIFIED IDENTITY]
        system block and must not be contradicted by a stale or incorrect memory-stored name.
        """
        relevant_memories = await self.retriever.retrieve_useful_context(user_id, current_request)

        if verified_name:
            # Remove any name-type memories so they can't compete with the verified DB name.
            relevant_memories = [
                m for m in relevant_memories
                if m.type not in (MemoryType.IDENTITY_NAME, MemoryType.IDENTITY)
            ]
            logger.debug(
                "identity_memories_suppressed",
                user_id=user_id,
                reason="verified_db_name_present",
                verified_name=verified_name,
            )

        return self.formatter.format_memories_for_prompt(relevant_memories)

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
from backend.lystra.memory.encryption import MemoryEncryption
from backend.crud.memory import memory as crud_memory
from backend.db.models.memory import Memory

logger = structlog.get_logger(__name__)

class DBMemoryStorage:
    """
    Task-scoped database storage.
    Uses an instance-level engine (QueuePool) to prevent TCP exhaustion on Windows.
    Must be explicitly disposed at the end of the task to prevent connection leaks
    and WinError 64 (due to event loop rotation in Celery).
    """

    def __init__(self):
        settings = get_settings()
        self.engine = create_async_engine(
            settings.DATABASE_URL, 
            pool_size=5, 
            pool_pre_ping=True
        )
        self.LocalSession = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def dispose(self):
        """Must be called to close the DB engine connections before the event loop closes."""
        await self.engine.dispose()

    @asynccontextmanager
    async def _session(self):
        try:
            async with self.LocalSession() as session:
                yield session
        except Exception:
            raise

    def _map_db_to_objects(self, mems: List[Memory]) -> List[MemoryObject]:
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
                remapped_type = LEGACY_TYPE_MAP.get(raw_type, raw_type)
                mem_type = MemoryType(remapped_type) if remapped_type else MemoryType.PREFERENCE
                
                # RAG: Safely transfer the embedding vector if it exists
                # In newer async pgvector, it might be an ndarray or list, converting to list
                emb = m.embedding.tolist() if hasattr(m.embedding, "tolist") else m.embedding
                
                obj = MemoryObject(
                    id=str(m.id),
                    user_id=str(m.user_id),
                    type=mem_type,
                    key=m.canonical_key or m.content[:50],
                    value=self.encryption.decrypt(m.content),
                    confidence=m.confidence,
                    importance=m.importance,
                    source="user_explicit",
                    status="active",
                    embedding=emb
                )
                objs.append(obj)
            except Exception as e:
                logger.warning("memory_conversion_failed", memory_id=str(m.id), error=str(e))
        return objs

    async def search_by_embedding(self, user_id: str, embedding: list[float], limit: int = 20):
        async with self._session() as db:
            mems = await crud_memory.search_by_embedding(
                db, 
                user_id=uuid.UUID(str(user_id)), 
                query_embedding=embedding, 
                limit=limit, 
                threshold=0.6
            )
            return self._map_db_to_objects(mems)

    async def fetch_active_memories(self, user_id):
        async with self._session() as db:
            now = datetime.now(timezone.utc)
            stmt = select(Memory).where(
                Memory.user_id == uuid.UUID(str(user_id)),
                Memory.status.in_(["active", "validated", "updated"]),
                or_(Memory.expires_at.is_(None), Memory.expires_at > now)
            )
            result = await db.execute(stmt)
            mems = result.scalars().all()
            return self._map_db_to_objects(mems)

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
            content_str = self.encryption.encrypt(str(memory.value)[:10000]) # Length cap and encryption
            update_data = {
                "content": content_str,
                "importance": memory.importance,
                "confidence": memory.confidence,
                "status": memory.status,
                "canonical_key": memory.key,
                "memory_type": memory.type.value if hasattr(memory.type, "value") else memory.type
            }
            if memory.embedding is not None:
                update_data["embedding"] = memory.embedding
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
                canonical_key=memory.key,
                embedding=memory.embedding
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
        self.encryption = MemoryEncryption()

    async def process_user_message(self, user_id: str, message: str, context_history: List[str], intent: str = "conversation", understanding=None):
        """
        Phase 1-9 & 20-30: Analyzes incoming messages, explicit feedback, and implicit signals to build memory.
        """
        # Phases 28, 29, 30: User Feedback & Learning
        if understanding:
            existing_memories_fallback = None
            
            async def get_memories():
                nonlocal existing_memories_fallback
                if existing_memories_fallback is None:
                    try:
                        emb = await self.extractor.llm.embed(message)
                        existing_memories_fallback = await self.storage.search_by_embedding(user_id, emb, limit=20)
                    except Exception:
                        existing_memories_fallback = await self.storage.fetch_active_memories(user_id)
                return existing_memories_fallback

            if getattr(understanding, "explicit_feedback", None):
                for feedback in understanding.explicit_feedback:
                    candidate = MemoryObject(
                        user_id=user_id, type=MemoryType.PREFERENCE, key="explicit_feedback",
                        value=feedback, status=MemoryStatus.ACTIVE, confidence=0.9, importance=0.8,
                        source=MemorySource.EXPLICIT
                    )
                    try:
                        candidate.embedding = await self.extractor.llm.embed(str(candidate.value))
                    except Exception:
                        pass
                    
                    mems = await get_memories()
                    conflict = await self.updater.find_semantic_conflict(candidate, mems, self.extractor.llm)
                    if conflict:
                        resolved = self.updater.resolve_conflict(conflict, candidate)
                        if not resolved.id: resolved.id = conflict.id
                        await self.storage.update_memory(resolved)
                    else:
                        await self.storage.add_memory(candidate)
                        
            if getattr(understanding, "implicit_feedback", None):
                for feedback in understanding.implicit_feedback:
                    candidate = MemoryObject(
                        user_id=user_id, type=MemoryType.PREFERENCE, key="implicit_feedback",
                        value=feedback, status=MemoryStatus.CANDIDATE, confidence=0.4, importance=0.5,
                        source=MemorySource.INFERRED
                    )
                    try:
                        candidate.embedding = await self.extractor.llm.embed(str(candidate.value))
                    except Exception:
                        pass
                        
                    mems = await get_memories()
                    conflict = await self.updater.find_semantic_conflict(candidate, mems, self.extractor.llm)
                    if conflict:
                        resolved = self.updater.resolve_conflict(conflict, candidate)
                        if not resolved.id: resolved.id = conflict.id
                        await self.storage.update_memory(resolved)
                    else:
                        await self.storage.add_memory(candidate)

        # Phase 20: Memory Extraction Timing
        if intent in ["greeting", "farewell", "acknowledgment"]:
            return

        # Phase 27: "Forget This" Semantics
        # Improve "forget" intent check
        msg_lower = message.lower()
        if "forget" in msg_lower.split() or "do not remember" in msg_lower or "delete that" in msg_lower:
            # RAG: Only fetch memories related to what we are trying to forget
            try:
                forget_embedding = await self.extractor.llm.embed(message)
                existing_memories = await self.storage.search_by_embedding(user_id, forget_embedding, limit=20)
                if not existing_memories:
                    existing_memories = await self.storage.fetch_active_memories(user_id)
            except Exception as e:
                logger.warning("rag_forget_search_failed", error=str(e))
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
        # RAG: Use vector search to find only relevant memories for conflict resolution 
        # instead of loading the user's entire life history into memory.
        try:
            query_embedding = await self.extractor.llm.embed(message)
            existing_memories = await self.storage.search_by_embedding(user_id, query_embedding, limit=20)
            if not existing_memories:
                existing_memories = await self.storage.fetch_active_memories(user_id)
        except Exception as e:
            logger.warning("rag_conflict_search_failed", error=str(e))
            existing_memories = await self.storage.fetch_active_memories(user_id)

        candidate = await self.extractor.extract_candidate_memory(user_id, message, context_history)
        if candidate:
            conflict = await self.updater.find_semantic_conflict(candidate, existing_memories, self.extractor.llm)
            
            if conflict:
                resolved = self.updater.resolve_conflict(conflict, candidate)
                # Ensure the resolved memory retains the conflict ID so it actually updates
                if not resolved.id:
                    resolved.id = conflict.id
                
                # RAG: Generate embedding for the updated memory
                try:
                    resolved.embedding = await self.extractor.llm.embed(str(resolved.value))
                except Exception as e:
                    logger.warning("memory_embedding_failed", error=str(e))
                    
                await self.storage.update_memory(resolved)
            else:
                # RAG: Generate embedding for the new memory
                try:
                    candidate.embedding = await self.extractor.llm.embed(str(candidate.value))
                except Exception as e:
                    logger.warning("memory_embedding_failed", error=str(e))
                    
                await self.storage.add_memory(candidate)
                
            # Phase 23: Memory Consolidation
            # It's safe to await here because process_user_message is ALREADY running
            # inside an execution_manager background task, so it doesn't block the stream.
            try:
                await self.updater.consolidate_memories(existing_memories, self.storage, self.extractor.llm)
            except Exception as e:
                logger.error("memory_consolidation_failed", error=str(e))

    async def get_contextual_prompt_injection(
        self, user_id: str, current_request: str, understanding=None, verified_name: str = ""
    ) -> str:
        """
        Phase 10-12: Retrieves relevant memories and formats them for natural personalization.

        verified_name: if set (from DB account record), any IDENTITY_NAME / IDENTITY memories
        are stripped before injection — the verified name is already in the [VERIFIED IDENTITY]
        system block and must not be contradicted by a stale or incorrect memory-stored name.
        """
        relevant_memories = await self.retriever.retrieve_useful_context(user_id, current_request, understanding)

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

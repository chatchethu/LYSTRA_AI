from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .base import CRUDBase
from backend.db.models.memory import Memory
from backend.schemas.memory import MemoryCreate, MemoryUpdate

class CRUDMemory(CRUDBase[Memory, MemoryCreate, MemoryUpdate]):
    async def get_user_memories(self, db: AsyncSession, user_id: UUID, memory_type: str = None, skip: int = 0, limit: int = 100) -> List[Memory]:
        query = select(Memory).filter(Memory.user_id == user_id)
        if memory_type:
            query = query.filter(Memory.memory_type == memory_type)
        result = await db.execute(query.order_by(Memory.importance.desc()).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def search_by_embedding(self, db: AsyncSession, user_id: UUID, query_embedding: list[float], limit: int = 5, threshold: float = 0.7) -> List[Memory]:
        # Using pgvector cosine distance `<=>`
        query = (
            select(Memory)
            .filter(Memory.user_id == user_id, Memory.embedding.is_not(None))
            .order_by(Memory.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_access(self, db: AsyncSession, memory_id: UUID, user_id: UUID) -> Optional[Memory]:
        mem = await self.get(db, id=memory_id)
        if mem and mem.user_id == user_id:
            mem.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(mem)
            return mem
        return None

    async def update_status(self, db: AsyncSession, memory_id: UUID, status: str, last_used_at: Optional[datetime] = None) -> None:
        from sqlalchemy import update
        values = {"status": status, "updated_at": datetime.now(timezone.utc)}
        if last_used_at:
            values["last_used_at"] = last_used_at
        stmt = update(Memory).where(Memory.id == memory_id).values(**values)
        await db.execute(stmt)

    async def touch_last_used(self, db: AsyncSession, memory_ids: List[UUID], ts: datetime) -> None:
        from sqlalchemy import update
        stmt = update(Memory).where(Memory.id.in_(memory_ids)).values(last_used_at=ts)
        await db.execute(stmt)

    async def update_memory_row(self, db: AsyncSession, memory_id: UUID, update_data: dict) -> None:
        from sqlalchemy import update
        if "updated_at" not in update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
        stmt = update(Memory).where(Memory.id == memory_id).values(**update_data)
        await db.execute(stmt)

memory = CRUDMemory(Memory)

from typing import List
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .base import CRUDBase
from backend.db.models.message import Message
from backend.schemas.message import MessageCreate

class CRUDMessage(CRUDBase[Message, MessageCreate, MessageCreate]):
    async def get_conversation_messages(self, db: AsyncSession, conversation_id: UUID, limit: int = 100) -> List[Message]:
        query = select(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_recent(self, db: AsyncSession, conversation_id: UUID, n: int) -> List[Message]:
        query = select(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(n)
        result = await db.execute(query)
        return list(reversed(result.scalars().all()))

message = CRUDMessage(Message)

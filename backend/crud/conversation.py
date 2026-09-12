from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from .base import CRUDBase
from backend.db.models.conversation import Conversation
from backend.schemas.conversation import ConversationCreate, ConversationUpdate

class CRUDConversation(CRUDBase[Conversation, ConversationCreate, ConversationUpdate]):
    async def get_user_conversations(self, db: AsyncSession, user_id: UUID, skip: int = 0, limit: int = 100) -> List[Conversation]:
        query = select(Conversation).filter(Conversation.user_id == user_id, Conversation.is_archived == False).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_with_messages(self, db: AsyncSession, id: UUID, user_id: UUID) -> Optional[Conversation]:
        query = select(Conversation).options(selectinload(Conversation.messages)).filter(Conversation.id == id, Conversation.user_id == user_id)
        result = await db.execute(query)
        return result.scalars().first()

    async def update_title(self, db: AsyncSession, id: UUID, title: str) -> Optional[Conversation]:
        conv = await self.get(db, id=id)
        if conv:
            conv.title = title
            await db.commit()
            await db.refresh(conv)
        return conv

    async def archive(self, db: AsyncSession, id: UUID) -> bool:
        conv = await self.get(db, id=id)
        if conv:
            conv.is_archived = True
            await db.commit()
            return True
        return False

conversation = CRUDConversation(Conversation)

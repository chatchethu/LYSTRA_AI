from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from backend.schemas.conversation import ConversationCreate, ConversationUpdate, ConversationResponse, ConversationWithMessages
from backend.schemas.message import MessageResponse
from backend.crud import conversation, message
from backend.auth.dependencies import get_db_session, get_current_user
from backend.db.models.user import User

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])

@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    return await conversation.get_user_conversations(db, user_id=current_user.id, skip=skip, limit=limit)

@router.post("", response_model=ConversationResponse)
async def create_conversation(
    conv_in: ConversationCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    conv_in.user_id = current_user.id
    return await conversation.create(db, obj_in=conv_in)

@router.get("/{id}", response_model=ConversationWithMessages)
async def get_conversation(
    id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    conv = await conversation.get_with_messages(db, id=id, user_id=current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.patch("/{id}", response_model=ConversationResponse)
async def update_conversation(
    id: UUID,
    conv_update: ConversationUpdate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    conv = await conversation.get(db, id=id, user_id=current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await conversation.update(db, db_obj=conv, obj_in=conv_update)

@router.delete("/{id}", status_code=204)
async def archive_conversation(
    id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    conv = await conversation.get(db, id=id, user_id=current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await conversation.archive(db, id=id)
    return None

@router.get("/{id}/messages", response_model=List[MessageResponse])
async def get_messages(
    id: UUID,
    limit: int = Query(100, ge=1),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user)
):
    conv = await conversation.get(db, id=id, user_id=current_user.id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await message.get_conversation_messages(db, conversation_id=id, limit=limit)

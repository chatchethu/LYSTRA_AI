from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

from backend.auth.dependencies import get_db_session, get_current_user, get_llm_gateway
from backend.db.models.user import User
from backend.crud.memory import memory as crud_memory
from backend.schemas.memory import MemoryResponse

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])

class MemoryCreateInput(BaseModel):
    content: str
    memory_type: str = "fact"
    importance: float = 0.5
    source: str = "manual"

class MemoryUpdateInput(BaseModel):
    content: Optional[str] = None
    memory_type: Optional[str] = None
    importance: Optional[float] = None
    status: Optional[str] = None

class SearchQuery(BaseModel):
    query: str
    limit: int = 10

@router.get("", response_model=List[MemoryResponse])
async def list_memories(
    memory_type: Optional[str] = None, 
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """List user memories with filters"""
    return await crud_memory.get_user_memories(db, user_id=user.id, memory_type=memory_type, skip=skip, limit=limit)

@router.post("", response_model=MemoryResponse)
async def add_memory(
    memory_in: MemoryCreateInput,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Manually add a memory"""
    from backend.schemas.memory import MemoryCreate
    obj_in = MemoryCreate(
        user_id=user.id,
        content=memory_in.content,
        memory_type=memory_in.memory_type,
        importance=memory_in.importance,
        source=memory_in.source,
        confidence=1.0,
        status="active"
    )
    mem = await crud_memory.create(db, obj_in=obj_in)
    await db.commit()
    await db.refresh(mem)
    return mem

@router.delete("/all/clear", status_code=204)
async def clear_all_memories(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Phase 25: Clear all user memories"""
    from sqlalchemy import delete
    from backend.db.models.memory import Memory
    await db.execute(delete(Memory).where(Memory.user_id == user.id))
    await db.commit()
    return None

@router.patch("/{id}", response_model=MemoryResponse)
async def update_memory(
    id: UUID,
    memory_in: MemoryUpdateInput,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Phase 25: Update memory"""
    mem = await crud_memory.get(db, id=id)
    if not mem or mem.user_id != user.id:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    update_data = memory_in.model_dump(exclude_unset=True)
    mem = await crud_memory.update(db, db_obj=mem, obj_in=update_data)
    await db.commit()
    return mem

@router.post("/{id}/disable", response_model=MemoryResponse)
async def disable_memory(
    id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Phase 25: Disable memory explicitly without deleting"""
    mem = await crud_memory.get(db, id=id)
    if not mem or mem.user_id != user.id:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    mem = await crud_memory.update(db, db_obj=mem, obj_in={"status": "disabled"})
    await db.commit()
    return mem


@router.delete("/{id}", status_code=204)
async def forget_memory(
    id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """Forget a memory"""
    mem = await crud_memory.get(db, id=id, user_id=user.id)
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found")
    await crud_memory.delete(db, id=id, user_id=user.id)
    return None



@router.get("/profile")
async def get_user_profile(
    user: User = Depends(get_current_user)
):
    """Get user profile preferences"""
    # Mock for now, expand later
    return {"profile": {"verbosity": "normal", "tone": "friendly"}}

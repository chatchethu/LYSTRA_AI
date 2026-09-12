with open('backend/api/memories.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Remove old MemoryService import
content = content.replace('from backend.memory.service import MemoryService\n', '')
content = content.replace('from backend.llm.gateway import LLMGateway\n', '')

old_post = '''@router.post("", response_model=MemoryResponse)
async def add_memory(
    memory_in: MemoryCreateInput,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    llm: LLMGateway = Depends(get_llm_gateway)
):
    """Manually add a memory"""
    # Use MemoryService to automatically generate embedding
    service = MemoryService(db, llm)
    return await service.store(
        user_id=user.id,
        content=memory_in.content,
        memory_type=memory_in.memory_type,
        importance=memory_in.importance,
        source=memory_in.source
    )'''

new_post = '''@router.post("", response_model=MemoryResponse)
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
    """Phase 25: Update memory / Disable memory (set status)"""
    mem = await crud_memory.get(db, id=id)
    if not mem or mem.user_id != user.id:
        raise HTTPException(status_code=404, detail="Memory not found")
        
    update_data = memory_in.model_dump(exclude_unset=True)
    mem = await crud_memory.update(db, db_obj=mem, obj_in=update_data)
    await db.commit()
    return mem
'''

content = content.replace(old_post, new_post)

# Remove the search_memories endpoint because it relies on old MemoryService
old_search = '''@router.post("/search", response_model=List[MemoryResponse])
async def search_memories(
    query: SearchQuery,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    llm: LLMGateway = Depends(get_llm_gateway)
):
    """Semantic search in memories"""
    service = MemoryService(db, llm)
    return await service.retrieve_relevant(user_id=user.id, query=query.query, limit=query.limit)'''

content = content.replace(old_search, '')

with open('backend/api/memories.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated memories.py APIs")

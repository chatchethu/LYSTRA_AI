import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models.file import FileChunk, File

async def retrieve_document_chunks(
    db: AsyncSession,
    user_id: uuid.UUID,
    query_embedding: List[float],
    limit: int = 5,
    min_similarity: float = 0.5,
    file_id: Optional[uuid.UUID] = None
) -> List[FileChunk]:
    """
    PHASE 35 - DOCUMENT RETRIEVAL
    query embedding -> user filtering -> vector similarity -> metadata filtering -> ranking
    Never retrieve documents from another user.
    """
    
    # 1. User Filtering (Join with File to ensure we only get the user's files)
    conditions = [
        File.user_id == user_id,
        FileChunk.embedding.is_not(None)
    ]
    
    if file_id:
        conditions.append(FileChunk.file_id == file_id)
        
    distance = FileChunk.embedding.cosine_distance(query_embedding)
    
    stmt = (
        select(FileChunk)
        .join(File, FileChunk.file_id == File.id)
        .where(*conditions)
        .where(distance <= (1.0 - min_similarity))
        .order_by(distance)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    chunks = result.scalars().all()
    
    return list(chunks)

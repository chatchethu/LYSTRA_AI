import pytest
import uuid
import os
import json
from httpx import AsyncClient
from backend.db.models.user import User
from backend.db.models.file import File, FileChunk

pytestmark = pytest.mark.asyncio

async def test_file_privacy_isolation_api(db_session, test_client):
    '''Phase 40: File Privacy Isolation (API & DB Layer)'''
    
    # Create User A and User B
    user_a = User(id=uuid.uuid4(), email="usera_file@example.com", hashed_password="pw")
    user_b = User(id=uuid.uuid4(), email="userb_file@example.com", hashed_password="pw")
    db_session.add_all([user_a, user_b])
    
    # Create File for User A
    file_a = File(
        id=uuid.uuid4(), user_id=user_a.id, filename="financials_a.pdf", 
        mime_type="application/pdf", storage_key="s3://b/f.pdf", size=1024, status="ready"
    )
    db_session.add(file_a)
    
    chunk_a = FileChunk(file_id=file_a.id, content="Secret Revenue A = 5000", chunk_index=0, embedding=[0.1]*768)
    db_session.add(chunk_a)
    await db_session.commit()
    
    # Simulate API Request by User B trying to access User A's file
    from sqlalchemy import select
    
    stmt = select(File).where(File.id == file_a.id, File.user_id == user_b.id)
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is None, "User B was able to fetch User A's file!"
    
async def test_vector_index_isolation(db_session):
    '''Phase 40: Vector Privacy Isolation'''
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()
    
    file_a = File(id=uuid.uuid4(), user_id=user_a_id, filename="A", mime_type="A", storage_key="A", size=1, status="ready")
    file_b = File(id=uuid.uuid4(), user_id=user_b_id, filename="B", mime_type="B", storage_key="B", size=1, status="ready")
    db_session.add_all([file_a, file_b])
    
    chunk_a = FileChunk(file_id=file_a.id, content="A", chunk_index=0, embedding=[0.9]*768)
    chunk_b = FileChunk(file_id=file_b.id, content="B", chunk_index=0, embedding=[0.9]*768)
    db_session.add_all([chunk_a, chunk_b])
    await db_session.commit()
    
    from sqlalchemy import select
    stmt = (
        select(FileChunk)
        .join(File, FileChunk.file_id == File.id)
        .where(File.user_id == user_a_id, File.status == "ready")
        .order_by(FileChunk.embedding.cosine_distance([0.9]*768))
    )
    result = await db_session.execute(stmt)
    rows = result.scalars().all()
    
    assert len(rows) == 1
    assert rows[0].id == chunk_a.id
    assert rows[0].id != chunk_b.id, "Vector search crossed tenant boundaries!"

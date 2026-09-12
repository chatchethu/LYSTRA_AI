from typing import Optional
import hashlib
import json
from fastapi import Request, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.auth.dependencies import get_db_session, get_current_user
from backend.db.models.user import User
from backend.db.models.idempotency import IdempotencyKey
from datetime import datetime, timedelta

async def check_idempotency(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    user: User = Depends(get_current_user)
) -> Optional[dict]:
    """
    Phase 46: Checks Idempotency-Key header.
    Returns the cached result if the request was already processed.
    Raises an error if currently processing.
    Returns None if this is a new request.
    """
    idem_key = request.headers.get("Idempotency-Key")
    if not idem_key:
        return None
        
    # Read request body to hash
    body = await request.body()
    req_hash = hashlib.sha256(body).hexdigest()
    
    # Check DB
    stmt = select(IdempotencyKey).where(IdempotencyKey.key == idem_key, IdempotencyKey.user_id == user.id)
    result = await db.execute(stmt)
    idem_record = result.scalar_one_or_none()
    
    if idem_record:
        if idem_record.status == "completed":
            return idem_record.result
        elif idem_record.status == "started":
            # Check expiration
            if datetime.utcnow() > idem_record.expiration:
                # Expired lock, we can retry
                idem_record.request_hash = req_hash
                idem_record.expiration = datetime.utcnow() + timedelta(minutes=5)
                await db.commit()
                return None
            else:
                raise HTTPException(status_code=409, detail="Request is already processing.")
        
    # Create new record
    new_record = IdempotencyKey(
        key=idem_key,
        user_id=user.id,
        request_hash=req_hash,
        status="started",
        expiration=datetime.utcnow() + timedelta(minutes=5)
    )
    db.add(new_record)
    await db.commit()
    
    return None

async def save_idempotency_result(
    key: str,
    user_id,
    result: dict,
    db: AsyncSession
):
    stmt = select(IdempotencyKey).where(IdempotencyKey.key == key, IdempotencyKey.user_id == user_id)
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    if record:
        record.status = "completed"
        record.result = result
        await db.commit()


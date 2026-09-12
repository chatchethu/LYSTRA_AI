"""
File Upload & Analysis API — LYSTRA Multimodal V1
"""
from __future__ import annotations

import os
import uuid
import hashlib
from pathlib import Path
import boto3
import threading

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi.concurrency import run_in_threadpool

from backend.auth.dependencies import get_current_user, get_llm_gateway, get_db_session
from backend.db.models.user import User
from backend.db.models.file import File as DBFile
from backend.llm.gateway import LLMGateway
from backend.config import get_settings
from backend.multimodal.file_context import FileContext, FileType, FileStatus

from backend.api.rate_limit import MultiRateLimit, user_rate_limit, file_upload_limit

router = APIRouter(
    prefix="/api/v1/files", 
    tags=["files"],
    dependencies=[Depends(MultiRateLimit(user_rate_limit, file_upload_limit))]
)


class FileStatusResponse(BaseModel):
    file_id: str
    filename: str
    type: str
    status: str
    page_count: int | None = None
    chunk_count: int = 0
    error: str | None = None


def get_s3_client():
    settings = get_settings()
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

@router.post("/upload", response_model=FileStatusResponse)
async def upload_file(
    file: UploadFile = File(...),
    llm: LLMGateway = Depends(get_llm_gateway),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    """
    PHASE 32 - FILE UPLOAD PIPELINE
    stream input with hard limit, validate MIME, calculate SHA-256, store DB record, enqueue processor.
    Uploads directly to AWS S3.
    """
    settings = get_settings()
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    file_id = uuid.uuid4()
    safe_name = f"{file_id}_{os.path.basename(file.filename or 'file')}"
    s3_key = f"uploads/{current_user.id}/{safe_name}"
    
    # Check basic extension early
    from backend.multimodal.file_router import _ALLOWED_EXTENSIONS
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_EXTENSIONS and ext not in [".csv", ".txt", ".html", ".htm", ".json", ".xml", ".yaml", ".yml", ".md", ".py", ".js", ".ts", ".java", ".c", ".cpp", ".rs", ".go", ".sh", ".css"]:
        raise HTTPException(status_code=422, detail=f"File type '{ext}' is not supported.")
        
    s3_client = get_s3_client()
    hasher = hashlib.sha256()
    size = 0
    
    # We will spool the stream to a temporary file, hash it, and upload to S3, 
    # to avoid loading the whole file in RAM while still supporting streaming to S3.
    import tempfile
    
    temp_fd, temp_path = tempfile.mkstemp()
    try:
        with os.fdopen(temp_fd, "wb") as f:
            while chunk := await file.read(8192):
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=413, detail="File too large")
                hasher.update(chunk)
                f.write(chunk)
        
        sha256_hash = hasher.hexdigest()
        
        def upload_to_s3():
            s3_client.upload_file(temp_path, settings.AWS_S3_BUCKET, s3_key)
            
        await run_in_threadpool(upload_to_s3)
        storage_url = f"s3://{settings.AWS_S3_BUCKET}/{s3_key}"
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    # --- Persist DB ---
    new_file = DBFile(
        id=file_id,
        user_id=current_user.id,
        filename=file.filename or "upload",
        mime_type=file.content_type or "",
        storage_key=storage_url,
        size=size,
        file_hash=sha256_hash,
        status=FileStatus.PROCESSING.value
    )
    db.add(new_file)
    await db.commit()

    # --- Enqueue Celery Task ---
    from backend.workers.tasks import process_file_upload
    process_file_upload.delay(str(file_id))

    return FileStatusResponse(
        file_id=str(file_id),
        filename=new_file.filename,
        type=new_file.mime_type,
        status=new_file.status,
        chunk_count=0
    )


@router.get("/{file_id}", response_model=FileStatusResponse)
async def get_file_status(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID")

    stmt = select(DBFile).where(DBFile.id == file_uuid, DBFile.user_id == current_user.id).options(selectinload(DBFile.chunks))
    result = await db.execute(stmt)
    db_file = result.scalar_one_or_none()

    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    return FileStatusResponse(
        file_id=str(db_file.id),
        filename=db_file.filename,
        type=db_file.mime_type,
        status=db_file.status,
        chunk_count=len(db_file.chunks),
        error=db_file.error
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session)
):
    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file ID")

    stmt = select(DBFile).where(DBFile.id == file_uuid, DBFile.user_id == current_user.id)
    result = await db.execute(stmt)
    db_file = result.scalar_one_or_none()

    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Remove from S3
    if db_file.storage_key and db_file.storage_key.startswith("s3://"):
        try:
            s3_client = get_s3_client()
            settings = get_settings()
            key = db_file.storage_key.replace(f"s3://{settings.AWS_S3_BUCKET}/", "")
            
            def delete_from_s3():
                s3_client.delete_object(Bucket=settings.AWS_S3_BUCKET, Key=key)
            
            await run_in_threadpool(delete_from_s3)
        except Exception as e:
            print(f"[WARN] Failed to delete S3 object: {e}")

    db_file.status = "deleted"
    await db.delete(db_file)
    await db.commit()

    return {"status": "deleted", "file_id": file_id}


async def get_file_context(file_id: str, db: AsyncSession, user_id: uuid.UUID) -> FileContext | None:
    """PHASE 31 - FILE CONTEXT AUTHORIZATION"""
    from backend.multimodal.file_context import FileChunk as ContextChunk
    try:
        file_uuid = uuid.UUID(file_id)
    except ValueError:
        return None

    stmt = select(DBFile).where(DBFile.id == file_uuid, DBFile.user_id == user_id).options(selectinload(DBFile.chunks))
    result = await db.execute(stmt)
    db_file = result.scalar_one_or_none()
    
    if not db_file:
        return None

    file_type = FileType.IMAGE
    if "pdf" in db_file.mime_type.lower():
        file_type = FileType.PDF
    elif "word" in db_file.mime_type.lower() or "document" in db_file.mime_type.lower() or "docx" in db_file.mime_type.lower():
        file_type = FileType.DOCUMENT

    try:
        status_enum = FileStatus(db_file.status)
    except ValueError:
        status_enum = FileStatus.FAILED

    ctx_chunks = []
    for c in db_file.chunks:
        ctx_chunks.append(ContextChunk(
            chunk_type=c.metadata_.get("chunk_type", "text") if c.metadata_ else "text",
            content=c.content,
            page=c.metadata_.get("page") if c.metadata_ else None,
            section=c.metadata_.get("section") if c.metadata_ else None
        ))

    return FileContext(
        file_id=str(db_file.id),
        filename=db_file.filename,
        file_type=file_type,
        status=status_enum,
        chunks=ctx_chunks,
        page_count=None,
        error=db_file.error,
        disk_path=db_file.storage_key
    )


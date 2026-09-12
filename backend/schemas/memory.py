from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, AliasChoices
from typing import Optional

class MemoryBase(BaseModel):
    memory_type: str
    content: str
    canonical_key: Optional[str] = None
    importance: float = 0.5
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = "user_chat"
    expires_at: Optional[datetime] = None
    metadata_: dict = Field(default_factory=dict, validation_alias=AliasChoices("metadata_", "metadata"), serialization_alias="metadata")
    source_message_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    status: str = "active"
    embedding: Optional[list[float]] = None
class MemoryCreate(MemoryBase):
    user_id: UUID

class MemoryUpdate(BaseModel):
    memory_type: Optional[str] = None
    content: Optional[str] = None
    importance: Optional[float] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    source: Optional[str] = None
    expires_at: Optional[datetime] = None
    metadata_: Optional[dict] = Field(None, validation_alias=AliasChoices("metadata_", "metadata"), serialization_alias="metadata")
    source_message_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    status: Optional[str] = None
    embedding: Optional[list[float]] = None

class MemoryResponse(MemoryBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True, "populate_by_name": True}

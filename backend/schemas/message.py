from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, AliasChoices
from typing import Optional, List, Any, Dict

class MessageBase(BaseModel):
    role: str
    content: str
    tool_calls: Optional[List[Any]] = None
    tool_results: Optional[List[Any]] = None
    intent: Optional[str] = None
    model_used: Optional[str] = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    duration_ms: Optional[int] = None
    blocks: Optional[List[Dict[str, Any]]] = None
    request_id: Optional[str] = None
    task_id: Optional[UUID] = None
    metadata_: dict = Field(default_factory=dict, validation_alias=AliasChoices("metadata_", "metadata"), serialization_alias="metadata")

    
    model_config = {"protected_namespaces": ()}

class MessageCreate(MessageBase):
    conversation_id: UUID
    user_id: UUID

class MessageResponse(MessageBase):
    id: UUID
    conversation_id: UUID
    user_id: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True, "populate_by_name": True}

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=30000, strip_whitespace=True)
    conversation_id: Optional[UUID] = None

class ChatResponse(BaseModel):
    message: MessageResponse
    conversation_id: UUID

class StreamChunk(BaseModel):
    chunk: str
    is_done: bool

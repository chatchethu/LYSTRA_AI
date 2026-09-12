from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, AliasChoices
from typing import Optional, List
from .message import MessageResponse

class ConversationBase(BaseModel):
    title: str
    summary: Optional[str] = None
    intent_type: Optional[str] = None
    metadata_: dict = Field(default_factory=dict, validation_alias=AliasChoices("metadata_", "metadata"), serialization_alias="metadata")


class ConversationCreate(ConversationBase):
    user_id: Optional[UUID] = None

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    intent_type: Optional[str] = None
    is_archived: Optional[bool] = None
    metadata_: Optional[dict] = Field(None, validation_alias=AliasChoices("metadata_", "metadata"), serialization_alias="metadata")

class ConversationResponse(ConversationBase):
    id: UUID
    user_id: UUID
    message_count: int
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True, "populate_by_name": True}

class ConversationWithMessages(ConversationResponse):
    messages: List[MessageResponse] = Field(default_factory=list)

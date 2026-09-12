from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, AliasChoices
from typing import Optional, List

class TaskStep(BaseModel):
    step_number: int
    description: str
    status: str
    result: Optional[str] = None

class TaskBase(BaseModel):
    title: str
    goal: str
    status: str
    current_step: int = 0
    total_steps: Optional[int] = None
    steps: List[TaskStep] = Field(default_factory=list)
    metadata_: dict = Field(default_factory=dict, validation_alias=AliasChoices("metadata_", "metadata"), serialization_alias="metadata")


class TaskCreate(TaskBase):
    user_id: UUID
    conversation_id: Optional[UUID] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    current_step: Optional[int] = None
    steps: Optional[List[TaskStep]] = None
    result: Optional[str] = None
    error: Optional[str] = None
    metadata_: Optional[dict] = Field(None, validation_alias=AliasChoices("metadata_", "metadata"), serialization_alias="metadata")


class TaskResponse(TaskBase):
    id: UUID
    user_id: UUID
    conversation_id: Optional[UUID]
    result: Optional[str]
    error: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True, "populate_by_name": True}

class TaskStatus(BaseModel):
    task_id: UUID
    status: str
    current_step: int

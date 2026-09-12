import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field

class MemoryType(str, Enum):
    IDENTITY = "identity" # Legacy / General
    IDENTITY_NAME = "identity_name"
    IDENTITY_OTHER = "identity_other"
    PREFERENCE = "preference"
    COMMUNICATION = "communication_preference"
    PROJECT = "ongoing_project"
    RECURRING_TASK = "recurring_task"
    CONTEXT = "useful_context"
    TEMPORARY = "temporary_information"
    SENSITIVE = "sensitive_information"
    IRRELEVANT = "irrelevant_information"

class MemorySource(str, Enum):
    EXPLICIT = "user_explicit"
    INFERRED = "inferred"

class MemoryStatus(str, Enum):
    # Phase 8: Detailed Memory Lifecycle
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    ACTIVE = "active"
    UPDATED = "updated"
    SUPERSEDED = "superseded" # Phase 9: Conflict Resolution
    STALE = "stale"
    EXPIRED = "expired"
    DELETED = "deleted"

class MemoryObject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    type: MemoryType
    key: str
    value: Any
    
    # Phase 9: Conflict Resolution Tracking
    previous_value: Optional[Any] = None
    
    # Phase 6: Confidence
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Phase 7: Memory Importance
    importance: float = Field(ge=0.0, le=1.0, description="Semantic importance mapping (High, Medium, Low)")
    
    source: MemorySource
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: Optional[datetime] = None
    
    # Phase 8: Expiration for temporary information
    expires_at: Optional[datetime] = None
    
    status: MemoryStatus = Field(default=MemoryStatus.CANDIDATE)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # RAG Support
    embedding: Optional[list[float]] = None

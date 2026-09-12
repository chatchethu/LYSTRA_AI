from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class MemoryCandidate(BaseModel):
    content: str
    memory_type: str = "fact"
    importance: float = 0.5
    source: str = "auto"

class MemoryRecord(BaseModel):
    id: UUID
    user_id: UUID
    content: str
    memory_type: str
    importance: float
    source: str
    created_at: datetime
    updated_at: datetime

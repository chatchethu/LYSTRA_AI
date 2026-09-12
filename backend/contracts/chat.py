from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TopicState(BaseModel):
    current_topic: str
    is_transition: bool = False
    confidence: float = 1.0

class ContextSnapshot(BaseModel):
    short_term_history: List[Dict[str, Any]] = Field(default_factory=list)
    active_summary: str = ""
    active_task_id: Optional[str] = None
    topic_state: Optional[TopicState] = None

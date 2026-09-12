from pydantic import BaseModel, Field
from typing import Any, Dict

class AgentEvent(BaseModel):
    event_type: str
    data: Dict[str, Any] = Field(default_factory=dict)

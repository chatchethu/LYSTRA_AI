from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ModelRequest(BaseModel):
    messages: List[Dict[str, Any]]
    model: Optional[str] = None
    temperature: float = 0.7
    response_format: Optional[Dict[str, Any]] = None

class ModelResponse(BaseModel):
    content: str
    usage: Dict[str, int] = Field(default_factory=dict)
    finish_reason: str = "stop"

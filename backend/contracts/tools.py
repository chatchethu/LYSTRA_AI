from pydantic import BaseModel, Field
from typing import Dict, Any, Optional

class ToolCall(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    call_id: str

class ToolResult(BaseModel):
    call_id: str
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None

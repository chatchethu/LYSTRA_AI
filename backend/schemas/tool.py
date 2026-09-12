from uuid import UUID
from pydantic import BaseModel
from typing import Optional

class ToolInfo(BaseModel):
    name: str
    description: str
    version: str
    permission_level: str

class ToolCallRequest(BaseModel):
    tool_name: str
    input: dict
    task_id: Optional[UUID] = None

class ToolCallResponse(BaseModel):
    tool_name: str
    output: Optional[dict] = None
    status: str
    error: Optional[str] = None

class PermissionRequest(BaseModel):
    tool_name: str
    is_allowed: bool

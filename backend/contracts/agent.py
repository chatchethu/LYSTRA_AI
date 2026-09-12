from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from uuid import UUID

class AgentRequest(BaseModel):
    user_id: UUID
    conversation_id: UUID
    message: str
    stream: bool = False
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    file_id: Optional[str] = None

class AgentDecision(BaseModel):
    action_type: str = Field(description="direct_response, clarification, single_tool, multi_step_task")
    reasoning: str
    selected_tools: List[str] = Field(default_factory=list)
    tool_arguments: Dict[str, Any] = Field(default_factory=dict)

class AgentResponse(BaseModel):
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    file_id: Optional[str] = None
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)



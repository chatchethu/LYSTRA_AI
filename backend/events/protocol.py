from pydantic import BaseModel, Field
from typing import Any, Dict, Optional, Literal
from datetime import datetime

EventType = Literal[
    "run.started",
    "message.accepted",
    "agent.understanding",
    "agent.thinking",
    "agent.topic_changed",
    "agent.plan",
    "tool.started",
    "tool.progress",
    "tool.completed",
    "memory.retrieved",
    "message.delta",
    "message.replace",
    "message.structured",
    "task.waiting_approval",
    "task.updated",
    "message.completed",
    "run.completed",
    "run.failed",
    "run.cancelled"
]

class SSEEvent(BaseModel):
    event: EventType
    request_id: str
    conversation_id: str
    message_id: Optional[str] = None
    task_id: Optional[str] = None
    sequence: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = Field(default_factory=dict)

    def to_sse_string(self) -> str:
        data_str = self.model_dump_json()
        return f"id: {self.sequence}\nevent: {self.event}\ndata: {data_str}\n\n"

from typing import Optional, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime

class CanonicalEvent(BaseModel):
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    request_id: Optional[str] = None
    conversation_id: Optional[uuid.UUID] = None
    message_id: Optional[uuid.UUID] = None
    task_id: Optional[uuid.UUID] = None
    sequence: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any]

    def to_sse_string(self) -> str:
        """Format strictly according to SSE specification."""
        import json
        lines = []
        if self.event_id:
            lines.append(f"id: {self.event_id}")
        lines.append(f"event: {self.event_type}")
        
        # Merge ids into payload for the client
        full_payload = self.payload.copy()
        if self.conversation_id: full_payload["conversation_id"] = str(self.conversation_id)
        if self.message_id: full_payload["message_id"] = str(self.message_id)
        if self.task_id: full_payload["task_id"] = str(self.task_id)
        if self.request_id: full_payload["request_id"] = self.request_id
        
        lines.append(f"data: {json.dumps(full_payload)}")
        return "\n".join(lines) + "\n\n"

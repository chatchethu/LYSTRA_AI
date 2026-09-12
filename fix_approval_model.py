import os

with open('backend/db/models/permission.py', 'r', encoding='utf-8') as f:
    perm_content = f.read()

# Remove ApprovalRequestModel from permission.py
# Find start of class
import re
perm_content = re.sub(r'class ApprovalRequestModel.*?class ExecutionLogModel', 'class ExecutionLogModel', perm_content, flags=re.DOTALL)

with open('backend/db/models/permission.py', 'w', encoding='utf-8') as f:
    f.write(perm_content)

# Update approval.py to add missing fields
approval_content = '''import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    task_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=True)
    step_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    tool_name: Mapped[str] = mapped_column(String)
    arguments_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    risk_level: Mapped[str] = mapped_column(String, default="low")
    status: Mapped[str] = mapped_column(String, default="pending")
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # New fields for permissions flow
    tool_input: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    user: Mapped["User"] = relationship("User")
'''

with open('backend/db/models/approval.py', 'w', encoding='utf-8') as f:
    f.write(approval_content)

print("Fixed approval model collision.")

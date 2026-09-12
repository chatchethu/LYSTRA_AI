content = '''import uuid
from typing import Optional
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, ForeignKey, UniqueConstraint, DateTime, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class ToolPermission(Base):
    __tablename__ = "tool_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "tool_name", name="uq_tool_permissions_user_tool"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    tool_name: Mapped[str] = mapped_column(String)
    permission_level: Mapped[str] = mapped_column(String)
    risk_level: Mapped[str] = mapped_column(String)
    is_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class ApprovalRequestModel(Base):
    __tablename__ = "approval_requests"
    
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    tool_name: Mapped[str] = mapped_column(String)
    tool_input: Mapped[dict] = mapped_column(JSON)
    reason: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class ExecutionLogModel(Base):
    __tablename__ = "execution_logs"
    
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    tool_name: Mapped[str] = mapped_column(String)
    event_type: Mapped[str] = mapped_column(String, default="execution") # e.g. execution, permission_granted
    input_data: Mapped[dict] = mapped_column(JSON)
    success: Mapped[bool] = mapped_column(Boolean)
    duration_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
'''

with open('backend/db/models/permission.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated permission.py models")

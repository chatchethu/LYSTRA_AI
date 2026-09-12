import uuid
from typing import Optional
from sqlalchemy import String, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Conversation(Base):
    __tablename__ = "conversations"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String)
    summary: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    intent_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    message_count: Mapped[int] = mapped_column(default=0)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Phase 8: Topic and Task Separation
    active_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL", use_alter=True), nullable=True)
    
    previous_topic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    current_topic: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    topic_changed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    
    previous_intent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    current_intent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    intent_changed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    
    previous_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL", use_alter=True), nullable=True)
    current_task_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="SET NULL", use_alter=True), nullable=True)
    task_changed: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    metadata_: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[list["Message"]] = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

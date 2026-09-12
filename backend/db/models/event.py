import uuid
from typing import Optional
from datetime import datetime
from sqlalchemy import String, ForeignKey, JSON, Integer, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import Base

class Event(Base):
    __tablename__ = "events"
    
    event_type: Mapped[str] = mapped_column(String, index=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    aggregate_type: Mapped[str] = mapped_column(String(50), index=True)
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    event_type: Mapped[str] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    
    status: Mapped[str] = mapped_column(String, default="pending", index=True)

    __table_args__ = (
        Index('ix_outbox_unpublished', "published_at", "attempts"),
        {'extend_existing': True}
    )

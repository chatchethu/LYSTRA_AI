import uuid
import json
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models.event import OutboxEvent
from backend.events.schemas import CanonicalEvent

async def write_outbox_event(
    db: AsyncSession,
    event: CanonicalEvent,
    aggregate_type: str,
    aggregate_id: uuid.UUID
):
    """
    Writes an event into the outbox table as part of the current transaction.
    """
    event_dict = event.model_dump(mode="json")
    
    outbox_record = OutboxEvent(
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        event_type=event.event_type,
        payload=event_dict
    )
    db.add(outbox_record)
    # Note: we do NOT commit here. The caller commits the transaction.


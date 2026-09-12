import asyncio
import structlog
import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.session import AsyncSessionLocal
from backend.db.models.event import OutboxEvent
import json
import uuid
from datetime import datetime
import redis.asyncio as redis
from backend.config import get_settings

logger = structlog.get_logger(__name__)

async def publish_outbox_events():
    """
    Background worker that polls the outbox_events table and publishes to Redis Streams.
    """
    settings = get_settings()
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    while True:
        try:
            async with AsyncSessionLocal() as db:
                # Find unpublished events
                stmt = select(OutboxEvent).where(
                    OutboxEvent.published_at.is_(None),
                    OutboxEvent.attempts < 3
                ).order_by(OutboxEvent.created_at.asc()).limit(50)
                
                result = await db.execute(stmt)
                events = result.scalars().all()
                
                if not events:
                    await asyncio.sleep(0.5)
                    continue
                    
                for outbox_ev in events:
                    lock_key = f"outbox:publish-lock:{outbox_ev.id}"
                    lock_token = str(uuid.uuid4())
                    acquired = await redis_client.set(lock_key, lock_token, nx=True, ex=60)
                    if not acquired:
                        continue
                    try:
                        # Construct the stream key based on conversation or aggregate
                        # Usually, stream key is tied to the conversation for SSE
                        payload = outbox_ev.payload
                        conv_id = payload.get("conversation_id")
                        if conv_id:
                            stream_key = f"stream:conversation:{conv_id}"
                        else:
                            stream_key = f"stream:{outbox_ev.aggregate_type}:{outbox_ev.aggregate_id}"
                            
                        # Format the payload for Redis Stream (it expects dict of strings)
                        inner_payload = payload.get("payload", payload)
                        request_id = payload.get("request_id")
                        stream_payload = {
                            "event_type": outbox_ev.event_type,
                            "payload": json.dumps(inner_payload) if isinstance(inner_payload, dict) else str(inner_payload),
                            "request_id": str(request_id) if request_id else "",
                            "conversation_id": str(conv_id) if conv_id else str(outbox_ev.aggregate_id)
                        }
                        
                        # Add to Redis Stream
                        await redis_client.xadd(name=stream_key, fields=stream_payload)
                        await redis_client.xtrim(stream_key, maxlen=1000)
                        
                        # Mark published
                        outbox_ev.published_at = datetime.utcnow()
                    except Exception as e:
                        logger.error(f"Failed to publish outbox event {outbox_ev.id}: {e}")
                        outbox_ev.attempts += 1
                    finally:
                        await redis_client.eval(
                            "if redis.call('get', KEYS[1]) == ARGV[1] then "
                            "return redis.call('del', KEYS[1]) else return 0 end",
                            1,
                            lock_key,
                            lock_token,
                        )
                        
                await db.commit()
                
        except Exception as e:
            logger.error(f"Outbox publisher loop error: {e}")
            await asyncio.sleep(1)

def start_outbox_publisher():
    asyncio.create_task(publish_outbox_events())


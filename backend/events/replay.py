import asyncio
import json
import structlog
import logging
from typing import AsyncGenerator
import redis.asyncio as redis
from backend.events.schemas import CanonicalEvent

logger = structlog.get_logger(__name__)

async def stream_events(
    redis_client: redis.Redis,
    stream_key: str,
    last_event_id: str = "0-0",
    timeout_ms: int = 60000,
    request_id: str = None
) -> AsyncGenerator[str, None]:
    """
    Reads from a Redis Stream and yields SSE formatted strings.
    Phase 44: Redis Streams with Last-Event-ID support.
    """
    current_id = last_event_id if last_event_id else "0-0"
    
    while True:
        try:
            # XREAD block for events
            # Format: [[stream_key, [(msg_id, {fields}), ...]]]
            response = await redis_client.xread(
                streams={stream_key: current_id},
                count=10,
                block=timeout_ms
            )
            
            if not response:
                # Timeout, send a keep-alive comment
                yield ": keepalive\n\n"
                continue
                
            for stream_name, messages in response:
                for msg_id, fields in messages:
                    current_id = msg_id
                    
                    event_type = fields.get("event_type", "unknown")
                    payload_str = fields.get("payload", "{}")
                    msg_request_id = fields.get("request_id")
                    conv_id = fields.get("conversation_id")
                    
                    if request_id and msg_request_id and request_id != msg_request_id:
                        continue
                    
                    try:
                        payload = json.loads(payload_str)
                        if isinstance(payload, dict) and conv_id:
                            payload["conversation_id"] = conv_id
                    except:
                        payload = {}
                        
                    # Reconstruct CanonicalEvent to output SSE
                    # Use the Redis stream msg_id as the SSE id
                    sse_lines = [
                        f"id: {msg_id}",
                        f"event: {event_type}",
                        f"data: {json.dumps(payload)}\n\n"
                    ]
                    yield "\n".join(sse_lines)
                    
                    if event_type in ["run.completed", "run.failed", "run.cancelled"]:
                        # Also send [DONE] standard
                        yield "data: [DONE]\n\n"
                        return

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error reading stream {stream_key}: {e}")
            yield f"event: error\ndata: {json.dumps({'detail': str(e)})}\n\n"
            break

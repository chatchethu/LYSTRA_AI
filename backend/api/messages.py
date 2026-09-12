from backend.api.errors import APIException
from backend.schemas.errors import ErrorCode
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
import asyncio
import redis.asyncio as aioredis
import structlog

from backend.auth.dependencies import get_db_session, get_current_user, get_llm_gateway
from backend.db.models.user import User
from backend.db.models.conversation import Conversation
from backend.db.session import AsyncSessionLocal
from backend.llm.gateway import LLMGateway
from backend.schemas.message import ChatRequest, ChatResponse
from backend.config import get_settings
from backend.llm.model_router import ModelRouter

from backend.crud.conversation import conversation as crud_conversation
from backend.crud.message import message as crud_message
from backend.schemas.conversation import ConversationCreate, ConversationUpdate
from backend.schemas.message import MessageCreate
from backend.lystra.context.conversation_state import ConversationState

from backend.api.rate_limit import MultiRateLimit, user_rate_limit, model_usage_limit
from backend.events.replay import stream_events
from backend.events.schemas import CanonicalEvent
from backend.events.outbox import write_outbox_event

logger = structlog.get_logger(__name__)

router = APIRouter(
    tags=["chat"],
    dependencies=[Depends(MultiRateLimit(user_rate_limit, model_usage_limit))]
)

async def _get_or_create_conversation(db: AsyncSession, current_user: User, conversation_id=None) -> Conversation:
    if conversation_id:
        try:
            conv_uuid = conversation_id if isinstance(conversation_id, uuid.UUID) else uuid.UUID(str(conversation_id))
            conv = await crud_conversation.get(db, id=conv_uuid, user_id=current_user.id)
            if conv:
                return conv
            else:
                # Fix P2: Silent conversation fallback on bad conversation_id
                raise HTTPException(status_code=404, detail="Conversation not found")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid conversation ID format")

    return await crud_conversation.create(
        db, 
        obj_in=ConversationCreate(
            title="New Chat",
            user_id=current_user.id,
            metadata_={"state": ConversationState().model_dump()}
        )
    )

@router.post("/api/v1/chat/stream")
async def chat_stream(
    request: Request,
    chat_request: ChatRequest,
    llm: LLMGateway = Depends(get_llm_gateway),
    db: AsyncSession = Depends(get_db_session),
    # Fix P1: get_optional_current_user changed to get_current_user since auth is required
    current_user: User = Depends(get_current_user)
):
    try:
        from backend.api.idempotency import check_idempotency, save_idempotency_result
        idem_result = await check_idempotency(request, db, current_user)
        if idem_result is not None:
            return idem_result
            
        conv = await _get_or_create_conversation(db, current_user, chat_request.conversation_id)
        cid = conv.id
        request_id = request.headers.get("X-Chat-Request-ID") or str(uuid.uuid4())
        
        if conv.title == "New Chat" or not conv.title:
            truncated = chat_request.message[:30] + ("..." if len(chat_request.message) > 30 else "")
            await crud_conversation.update_title(db, id=cid, title=truncated)
        
        last_event_id = request.headers.get("Last-Event-ID")
        
        if not last_event_id:
            # New run
            user_msg = MessageCreate(
                role="user",
                content=chat_request.message,
                conversation_id=cid,
                user_id=current_user.id,
                metadata_={}
            )
            await crud_message.create(db, obj_in=user_msg)
            
            # Initial Events in outbox (outbox is for durability of terminal/critical events)
            # Ephemeral streaming chunks will be written directly (fire-and-forget) by the worker.
            ev_start = CanonicalEvent(
                event_type="run.started",
                request_id=request_id,
                conversation_id=cid,
                payload={}
            )
            ev_acc = CanonicalEvent(
                event_type="message.accepted",
                request_id=request_id,
                conversation_id=cid,
                payload={"message": chat_request.message}
            )
            await write_outbox_event(db, ev_start, "conversation", cid)
            await write_outbox_event(db, ev_acc, "conversation", cid)
            
            await db.commit()

            # Queue the actual AI work in Celery.
            from backend.workers.tasks import process_chat_task
            chat_req_dict = chat_request.model_dump()
            # Must pass original idempotency key to task if it needs it, but we can save result here
            idempotency_key = request.headers.get("Idempotency-Key")
            chat_req_dict["idempotency_key"] = idempotency_key
            
            try:
                process_chat_task.apply_async(
                    args=[
                        chat_req_dict,
                        str(current_user.id),
                        str(cid),
                        request_id,
                    ],
                    queue="interactive",
                )
                
                # Fix P0: Idempotency is half-baked
                if idempotency_key:
                    # Record that we successfully enqueued this task, so retries don't duplicate work
                    # Streaming Response itself isn't cacheable by JSON idempotency logic, so we save now.
                    await save_idempotency_result(request, db, current_user, key=idempotency_key, result={"status": "enqueued", "request_id": request_id, "conversation_id": str(cid)})
            except Exception as exc:
                import json
                settings = get_settings()
                error_redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
                try:
                    await error_redis.xadd(
                        name=f"stream:conversation:{cid}",
                        fields={
                            "event_type": "run.failed",
                            "payload": json.dumps({"error": "Unable to queue the chat task."}),
                            "request_id": request_id,
                        },
                    )
                finally:
                    await error_redis.aclose()
                logger.exception("chat_worker_unavailable", request_id=request_id)
                raise HTTPException(status_code=503, detail="Chat worker unavailable") from exc

        settings = get_settings()
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        stream_key = f"stream:conversation:{cid}"

        return StreamingResponse(
            stream_events(r, stream_key, last_event_id, request_id=request_id),
            media_type="text/event-stream",
            headers={"X-Chat-Request-ID": request_id},
        )
    except HTTPException:
        raise
    except Exception as e:
        # Fix P1: Internal exception strings leaked to client
        logger.exception("chat_stream_failed", conversation_id=str(chat_request.conversation_id))
        raise HTTPException(status_code=500, detail="Internal server error")

from pydantic import BaseModel

class CancelRequest(BaseModel):
    request_id: str

@router.post("/api/v1/chat/cancel")
async def cancel_chat_request(
    cancel_req: CancelRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Phase 48: Cancels an ongoing chat request by setting a Redis flag
    that the Celery worker checks periodically.
    """
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(get_settings().REDIS_URL, decode_responses=True)
        try:
            # Fix P2: Ownership check on /chat/cancel request_id using user_id namespace
            await r.set(f"cancel:request:{current_user.id}:{cancel_req.request_id}", "1", ex=3600)
        finally:
            # Fix P3: Redis client leak on error path
            await r.aclose()
        return {"status": "success", "message": "Cancellation requested."}
    except Exception as e:
        logger.exception("cancel_chat_failed", request_id=cancel_req.request_id)
        raise HTTPException(status_code=500, detail="Internal server error")



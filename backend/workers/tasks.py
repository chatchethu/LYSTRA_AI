import asyncio
import uuid
import structlog
import logging
import json
from backend.workers.celery_app import celery_app
from backend.db.session import AsyncSessionLocal
from backend.config import get_settings

logger = structlog.get_logger(__name__)

@celery_app.task(bind=True, max_retries=3, queue='agent_tasks')
def delete_user_data_task(self, user_id: str):
    # Fix P0: delete_user_data_task is a no-op
    raise NotImplementedError("delete_user_data_task not yet implemented")

# Fix P2: Added soft_time_limit and time_limit to prevent wedging workers
@celery_app.task(bind=True, max_retries=3, queue='interactive', soft_time_limit=600, time_limit=660)
def process_chat_task(self, chat_request_dict: dict, user_id: str, conversation_id: str, request_id: str):
    asyncio.run(_process_chat_async(chat_request_dict, user_id, conversation_id, request_id))

async def _process_chat_async(chat_request_dict: dict, user_id: str, conversation_id: str, request_id: str):
    import redis.asyncio as aioredis
    settings = get_settings()
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    stream_key = f"stream:conversation:{conversation_id}"
    cancel_key = f"cancel:request:{user_id}:{request_id}"
    
    try:
        from backend.llm.ollama_provider import OllamaProvider
        from backend.llm.gateway import LLMGateway
        from backend.lystra.orchestration.execution_manager import ExecutionManager
        from backend.crud.message import message as crud_message
        from backend.schemas.message import MessageCreate
        
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
        from sqlalchemy import pool
        
        # Fix P2: Use NullPool so we don't exhaust global DB connections by making a full pool per task
        local_engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, poolclass=pool.NullPool)
        LocalSession = async_sessionmaker(local_engine, class_=AsyncSession, expire_on_commit=False)
        
        async with LocalSession() as db:
            # Fix P3: Idempotency protection inside the task itself
            from sqlalchemy import select
            from backend.db.models.message import Message
            stmt = select(Message).where(Message.request_id == request_id, Message.role == "assistant")
            existing_msg = (await db.execute(stmt)).scalars().first()
            if existing_msg:
                logger.info("task_idempotency_hit", request_id=request_id)
                # Task already ran to completion, just exit successfully
                return
            
            # Fetch history
            history = await crud_message.get_conversation_messages(db, conversation_id=uuid.UUID(conversation_id))
            history_dicts = [{"role": m.role, "content": m.content} for m in history]
            
            # Init pipeline
            bg_llm = LLMGateway(OllamaProvider())
            execution_manager = ExecutionManager(bg_llm)
            
            chat_message = chat_request_dict.get("message", "")
            
            await r.xadd(stream_key, {
                "event_type": "message.chunk",
                "payload": json.dumps({"delta": ""}),
                "request_id": request_id
            })
            
            # Real execution via stream
            final_response = ""
            async for chunk in execution_manager.execute_stream(user_id=user_id, user_message=chat_message, chat_history=history_dicts):
                # Fix P0: Cancel polling actually checks the redis flag
                if await r.get(cancel_key):
                    logger.info("run_cancelled_by_user", request_id=request_id)
                    await r.xadd(stream_key, {
                        "event_type": "run.cancelled", 
                        "payload": json.dumps({}), 
                        "request_id": request_id
                    })
                    return # Exit the task early
                    
                final_response += chunk
                await r.xadd(stream_key, {
                    "event_type": "message.chunk",
                    "payload": json.dumps({"delta": chunk}),
                    "request_id": request_id
                })
            
            # Save assistant message — only if we actually got a response.
            # If execute_stream raised (prepare_turn_failed, llm_stream_failed),
            # final_response is empty and we must NOT write a blank/error row to the DB.
            if final_response.strip():
                asst_msg = MessageCreate(
                    role="assistant",
                    content=final_response,
                    conversation_id=uuid.UUID(conversation_id),
                    user_id=uuid.UUID(user_id),
                    request_id=request_id
                )
                await crud_message.create(db, obj_in=asst_msg)
                await db.commit()
            
            # Only emit completion events if we actually produced content.
            # If execution failed (exception raised inside execute_stream), 
            # the except block below emits run.failed instead.
            if final_response.strip():
                await r.xadd(stream_key, {
                    "event_type": "message.completed",
                    "payload": json.dumps({"content": final_response}),
                    "request_id": request_id
                })
                await r.xadd(stream_key, {
                    "event_type": "run.completed",
                    "payload": json.dumps({}),
                    "request_id": request_id
                })

            # Fix P1: Engine is disposed AFTER awaiting background tasks
            pending = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            if pending:
                logger.info("awaiting_background_tasks", count=len(pending))
                await asyncio.gather(*pending, return_exceptions=True)
                
            await local_engine.dispose()
                
    except Exception as e:
        # Fix P1: Task failures swallowed, Internal exception leaked
        logger.exception("chat_task_failed", conversation_id=conversation_id, request_id=request_id)
        await r.xadd(stream_key, {
            "event_type": "run.failed",
            "payload": json.dumps({"error": "Internal server error"}),
            "request_id": request_id
        })
        raise # Let Celery see the failure, trigger retry/alerting
    finally:
        try:
            if 'execution_manager' in locals():
                await execution_manager.shutdown()
        except Exception as cleanup_err:
            logger.warning("execution_manager_shutdown_failed", exc_info=True)
            
        try:
            if 'local_engine' in locals():
                await local_engine.dispose()
        except Exception as cleanup_err:
            # Fix P3: Bare except in cleanup
            logger.warning("engine_dispose_failed", exc_info=True)
        await r.aclose()

@celery_app.task(bind=True, max_retries=3)
def execute_agent_task(self, task_id: str, user_id: str):
    # Fix P0
    raise NotImplementedError("execute_agent_task not yet implemented")

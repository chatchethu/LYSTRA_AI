import time
from uuid import UUID
from datetime import datetime, timezone
from jsonschema import validate, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
import structlog

from .registry import registry, ToolResult, ToolRiskLevel
from .permissions import PermissionManager, _redact_input
from backend.db.models.approval import ApprovalRequest as ApprovalRequestModel

logger = structlog.get_logger(__name__)

class ToolExecutor:
    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager
        
    async def execute(
        self,
        db: AsyncSession,
        user_id: UUID,
        tool_name: str,
        arguments: dict,
        approval_id: UUID = None,
        task_id: UUID = None,
        conversation_id: UUID = None,
        request_id: UUID = None
    ) -> ToolResult:
        start_time = time.time()
        
        # 1. Check if tool exists
        tool = registry.get_tool(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data={},
                error=f"Tool {tool_name} not found in registry",
                metadata={"execution_time_ms": (time.time() - start_time) * 1000}
            )

        from backend.config import get_settings
        settings = get_settings()

        # Phase 82: Shadow Mode Block
        if getattr(settings, 'SHADOW_MODE', False):
            if tool.risk_level in [ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]:
                logger.info("shadow_mode_blocked", tool=tool_name, user_id=str(user_id))
                result = ToolResult(
                    success=True,
                    data={"shadow_mode": True, "note": "Execution was simulated in shadow mode."},
                    metadata={"execution_time_ms": 0}
                )
                # Fix #3: Log shadow mode blocks securely to DB audit trace
                try:
                    await self.permission_manager.log_execution(db, user_id, tool_name, arguments, result, 0, event_type="shadow_mode_blocked")
                except Exception as log_err:
                    logger.error("execution_log_failed", tool=tool_name, error=str(log_err))
                return result

        # 2. Check arguments against schema (Schema Validation)
        try:
            schema = tool.get_schema()
        except Exception as e:
            # Fix #5: Broaden schema-generation exceptions
            return ToolResult(success=False, data=None, error=f"Tool schema error: {e}")
            
        try:
            validate(instance=arguments, schema=schema)
        except ValidationError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Schema validation failed: {e.message}"
            )
            
        # 3. Check permissions & risk level
        if approval_id:
            stmt = select(ApprovalRequestModel).where(ApprovalRequestModel.id == approval_id)
            res = await db.execute(stmt)
            req = res.scalar_one_or_none()
            
            # Basic ownership and status matching
            if not req or req.status != "approved" or req.user_id != user_id or req.tool_name != tool_name:
                return ToolResult(success=False, data=None, error="Approval request not found, denied, or mismatch.")
                
            # Fix #6: Enforce Approval Expiry (e.g. 1 hour TTL)
            ttl_seconds = 3600
            if req.resolved_at and (datetime.now(timezone.utc) - req.resolved_at).total_seconds() > ttl_seconds:
                return ToolResult(success=False, data=None, error="Approval has expired.")
                
            # Fix #1: Approved arguments scoping payload check
            redacted_arguments = _redact_input(arguments)
            if req.tool_input != redacted_arguments:
                logger.warning("approval_argument_mismatch", requested=redacted_arguments, approved=req.tool_input)
                return ToolResult(success=False, data=None, error="Approved arguments do not match execution request.")
        else:
            perm_res = await self.permission_manager.check_permission(db, user_id, tool_name, tool.risk_level)
            if not perm_res.allowed:
                if tool.risk_level in [ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]:
                    return ToolResult(success=False, data=None, error=f"ApprovalRequired: {perm_res.reason}")
                return ToolResult(success=False, data=None, error=f"Permission denied: {perm_res.reason}")
                
        # 4. Limits
        # Fix #8: Warn loudly if deploying without rate limits
        logger.warning("rate_limiting_not_implemented", tool=tool_name, user_id=str(user_id))
        
        # 5. Execute
        try:
            result = await tool.execute(
                user_id=user_id,
                task_id=task_id,
                conversation_id=conversation_id,
                request_id=request_id,
                **arguments
            )
            if not isinstance(result, ToolResult):
                result = ToolResult(success=True, data=result)
        except Exception as e:
            result = ToolResult(success=False, data=None, error=f"Execution error: {str(e)}")
            
        # Fix #2: Single-use consumption (Burn the approval ID after successful execution)
        if approval_id and result.success:
            try:
                stmt = update(ApprovalRequestModel).where(ApprovalRequestModel.id == approval_id).values(
                    status="consumed",
                    resolved_at=datetime.now(timezone.utc)
                )
                await db.execute(stmt)
                await db.commit()
            except Exception as e:
                logger.error("approval_burn_failed", error=str(e), approval_id=str(approval_id))
            
        # 6. Log execution
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Fix #4: Catch DB Audit exceptions to prevent masking success
        try:
            await self.permission_manager.log_execution(db, user_id, tool_name, arguments, result, duration_ms, approval_request_id=approval_id)
        except Exception as log_err:
            logger.error("execution_log_failed", tool=tool_name, error=str(log_err))
            
        return result

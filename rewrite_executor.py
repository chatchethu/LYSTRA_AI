content = '''import time
from uuid import UUID
from jsonschema import validate, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .registry import registry, ToolResult, ToolRiskLevel
from .permissions import PermissionManager
from backend.db.models.permission import ApprovalRequestModel

class ToolExecutionError(Exception):
    pass

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
        # Dangerous external side effects are blocked in shadow mode
        if getattr(settings, 'SHADOW_MODE', False):
            if tool.risk_level in [ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]:
                import structlog
                logger = structlog.get_logger(__name__)
                logger.info(
                    "shadow_mode_blocked",
                    tool=tool_name,
                    user_id=str(user_id)
                )
                return ToolResult(
                    success=True,
                    data={"shadow_mode": True, "note": "Execution was simulated in shadow mode."},
                    metadata={"execution_time_ms": 0}
                )

        # 2. Check arguments against schema (Schema Validation)
        try:
            schema = tool.get_schema()
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
            if not req or req.status != "approved" or req.user_id != user_id or req.tool_name != tool_name:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Approval request not found, denied, or mismatch."
                )
        else:
            perm_res = await self.permission_manager.check_permission(db, user_id, tool_name, tool.risk_level)
            if not perm_res.allowed:
                if tool.risk_level in [ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"ApprovalRequired: {perm_res.reason}"
                    )
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Permission denied: {perm_res.reason}"
                )
                
        # 4. Limits - Placeholder for rate limiting
        # TODO: Implement rate limiting per user/tool
        
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
                # Legacy tool support or wrapping
                result = ToolResult(success=True, data=result)
        except Exception as e:
            result = ToolResult(success=False, data=None, error=f"Execution error: {str(e)}")
            
        # 6. Log execution
        duration_ms = int((time.time() - start_time) * 1000)
        await self.permission_manager.log_execution(db, user_id, tool_name, arguments, result, duration_ms)
        
        return result
'''

with open('backend/tools/executor.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated executor.py")

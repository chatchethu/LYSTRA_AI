from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from uuid import UUID
from pydantic import BaseModel

from backend.db.models.user import User
from backend.auth.dependencies import get_current_user
from backend.api.rate_limit import MultiRateLimit, user_rate_limit, tool_usage_limit

router = APIRouter(
    prefix="/api/v1/tools", 
    tags=["tools"],
    dependencies=[Depends(MultiRateLimit(user_rate_limit, tool_usage_limit))]
)

from backend.tools import registry, PermissionManager, ToolExecutor, ToolResult
from backend.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession

permission_manager = PermissionManager()
executor = ToolExecutor(permission_manager)

class ToolInfo(BaseModel):
    name: str
    description: str
    version: str
    permission_level: str
    risk_level: str
    requires_approval: bool

@router.get("", response_model=List[ToolInfo])
async def list_tools():
    tools = registry.get_all_tools()
    return [
        ToolInfo(
            name=t.name,
            description=t.description,
            version=t.version,
            permission_level=t.permission_level.value,
            risk_level=t.risk_level.value,
            requires_approval=t.requires_approval
        ) for t in tools
    ]

@router.get("/{name}", response_model=ToolInfo)
async def get_tool(name: str):
    tool = registry.get_tool(name)
    if not tool:
        raise HTTPException(status_code=404, detail="Tool not found")
    return ToolInfo(
        name=tool.name,
        description=tool.description,
        version=tool.version,
        permission_level=tool.permission_level.value,
        risk_level=tool.risk_level.value,
        requires_approval=tool.requires_approval
    )

class ExecutionRequest(BaseModel):
    kwargs: Dict[str, Any]

@router.post("/{name}/execute", response_model=ToolResult)
async def execute_tool(name: str, request: ExecutionRequest, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await executor.execute(db, current_user.id, name, request.kwargs)
    return result

@router.get("/permissions/me")
async def get_permissions(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from backend.db.models.permission import ToolPermission
    stmt = select(ToolPermission).where(ToolPermission.user_id == current_user.id)
    result = await db.execute(stmt)
    perms = result.scalars().all()
    return {"permissions": {p.tool_name: p.permission_level for p in perms if p.is_allowed}}

@router.post("/permissions/{tool_name}")
async def grant_permission(tool_name: str, level: str, risk_level: str = "low", current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await permission_manager.grant_permission(db, current_user.id, tool_name, level, risk_level)
    return {"status": "success"}

@router.delete("/permissions/{tool_name}")
async def revoke_permission(tool_name: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    await permission_manager.revoke_permission(db, current_user.id, tool_name)
    return {"status": "success"}

@router.get("/approvals/pending")
async def get_pending_approvals(current_user: User = Depends(get_current_user)):
    return await permission_manager.get_pending_approvals(current_user.id)

@router.post("/approvals/{approval_id}/approve")
async def approve_request(approval_id: UUID, current_user: User = Depends(get_current_user)):
    await permission_manager.approve(approval_id, current_user.id)
    return {"status": "approved"}

@router.post("/approvals/{approval_id}/deny")
async def deny_request(approval_id: UUID, reason: str, current_user: User = Depends(get_current_user)):
    await permission_manager.deny(approval_id, current_user.id, reason)
    return {"status": "denied"}

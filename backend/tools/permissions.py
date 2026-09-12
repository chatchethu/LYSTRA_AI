from uuid import UUID
from typing import Dict, List, Any
from datetime import datetime, timezone
import time
import uuid
import structlog

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.exc import IntegrityError

from backend.db.models.permission import ToolPermission, ExecutionLogModel
from backend.db.models.approval import ApprovalRequest as ApprovalRequestModel
from .registry import ToolRiskLevel, ToolResult, registry
from pydantic import BaseModel

logger = structlog.get_logger(__name__)

class PermissionResult(BaseModel):
    allowed: bool
    reason: str

class ApprovalRequest(BaseModel):
    id: UUID
    user_id: UUID
    tool_name: str
    tool_input: dict
    reason: str
    status: str

# Fix #4: SENSITIVE_KEYS substring matching
SENSITIVE_SUBSTRINGS = {"password", "token", "secret", "api_key", "apikey", "ssn", "credit_card", "private_key", "authorization"}

def _is_sensitive(key: str) -> bool:
    k = key.lower().replace("_", "").replace("-", "")
    return any(s.replace("_", "") in k for s in SENSITIVE_SUBSTRINGS)

# Fix #3: _redact_input missing list recursion
def _redact_input(data: Any) -> Any:
    if isinstance(data, dict):
        return {
            k: ("***REDACTED***" if _is_sensitive(k) else _redact_input(v))
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [_redact_input(v) for v in data]
    return data

from enum import Enum

class PermissionStatus(Enum):
    NONE = "none"
    GRANTED = "granted"
    DENIED = "denied"
    PENDING_APPROVAL = "pending_approval"

def _resolve_permission_state(perm: ToolPermission, risk_level: ToolRiskLevel) -> PermissionStatus:
    if not perm:
        if risk_level in [ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]:
            return PermissionStatus.PENDING_APPROVAL
        return PermissionStatus.GRANTED
        
    if not perm.is_allowed:
        return PermissionStatus.DENIED
        
    if perm.requires_approval and risk_level in [ToolRiskLevel.HIGH, ToolRiskLevel.CRITICAL]:
        return PermissionStatus.PENDING_APPROVAL
        
    return PermissionStatus.GRANTED

class PermissionManager:
    """
    Controls tool access with RBAC, risk-based approval, and audit logging.
    HIGH/CRITICAL risk tools require explicit user approval.
    """
        
    async def check_permission(self, db: AsyncSession, user_id: UUID, tool_name: str, provided_risk_level: ToolRiskLevel = None) -> PermissionResult:
        # Fix #2: Fail-open default (LOW risk) for unregistered tools
        tool = registry.get_tool(tool_name)
        if not tool:
            logger.error("unregistered_tool_permission_check", tool_name=tool_name)
            return PermissionResult(allowed=False, reason="Unknown tool — cannot verify risk level")
            
        authoritative_risk = tool.risk_level
        if provided_risk_level and provided_risk_level != authoritative_risk:
            logger.warning("tool_risk_mismatch", tool_name=tool_name, provided=provided_risk_level, authoritative=authoritative_risk)
            
        risk_level = authoritative_risk

        # Check DB for explicit deny/allow
        stmt = select(ToolPermission).where(
            and_(
                ToolPermission.user_id == user_id,
                ToolPermission.tool_name == tool_name
            )
        )
        result = await db.execute(stmt)
        perm = result.scalar_one_or_none()

        # Fix #6: Make approval logic clear with explicit state machine
        status = _resolve_permission_state(perm, risk_level)
        
        if status == PermissionStatus.DENIED:
            return PermissionResult(allowed=False, reason="Explicitly denied by user")
            
        if status == PermissionStatus.PENDING_APPROVAL:
            return PermissionResult(allowed=False, reason="High risk tool requires explicit approval")

        # Status is GRANTED
        # Fix #7: One-time permission enforcement
        if perm and getattr(perm, "permission_level", "") == "one_time":
            await self.revoke_permission(db, user_id, tool_name)
            return PermissionResult(allowed=True, reason="One-time permission consumed")

        return PermissionResult(allowed=True, reason="Allowed")

    async def request_approval(self, db: AsyncSession, user_id: UUID, tool_name: str, tool_input: dict, reason: str) -> ApprovalRequest:
        req_id = uuid.uuid4()
        req = ApprovalRequestModel(
            id=req_id,
            user_id=user_id,
            tool_name=tool_name,
            tool_input=_redact_input(tool_input),
            reason=reason,
            status="pending"
        )
        db.add(req)
        await db.commit()
        await db.refresh(req)
        return ApprovalRequest(
            id=req.id,
            user_id=req.user_id,
            tool_name=req.tool_name,
            tool_input=req.tool_input,
            reason=req.reason,
            status=req.status
        )

    async def approve(self, db: AsyncSession, approval_request_id: UUID, user_id: UUID) -> ApprovalRequest:
        stmt = select(ApprovalRequestModel).where(ApprovalRequestModel.id == approval_request_id)
        res = await db.execute(stmt)
        req = res.scalar_one_or_none()
        
        if not req:
            raise LookupError("Approval request not found.")
        if req.user_id != user_id:
            raise PermissionError("This approval request does not belong to the requesting user.")
        if req.status != "pending":
            raise ValueError(f"Approval request already {req.status}.")

        req.status = "approved"
        req.resolved_at = datetime.now(timezone.utc)
        
        # Fix #5: Explicit commit
        await db.commit()
        
        tool = registry.get_tool(req.tool_name)
        # Fix #1: risk_level=req.reason bug
        # Use authoritative risk level from tool or default to HIGH
        risk_level = getattr(tool.risk_level, "value", str(tool.risk_level)) if tool else getattr(ToolRiskLevel.HIGH, "value", "high")
        
        # Grant real permission in DB
        await self.grant_permission(
            db, 
            user_id=user_id, 
            tool_name=req.tool_name, 
            permission_level="one_time", 
            risk_level=risk_level
        )
        
        # Fix #8: Link log to approval_request via metadata or input
        await self.log_execution(db, user_id, req.tool_name, {"approval_request_id": str(req.id)}, ToolResult(success=True, data="Approval Granted"), 0, event_type="approval_approved")
        
        return ApprovalRequest(
            id=req.id, user_id=req.user_id, tool_name=req.tool_name, 
            tool_input=req.tool_input, reason=req.reason, status=req.status
        )

    async def deny(self, db: AsyncSession, approval_request_id: UUID, user_id: UUID, reason: str) -> ApprovalRequest:
        stmt = select(ApprovalRequestModel).where(ApprovalRequestModel.id == approval_request_id)
        res = await db.execute(stmt)
        req = res.scalar_one_or_none()
        
        if not req:
            raise LookupError("Approval request not found.")
        if req.user_id != user_id:
            raise PermissionError("This approval request does not belong to the requesting user.")
        if req.status != "pending":
            raise ValueError(f"Approval request already {req.status}.")

        req.status = "denied"
        req.reason = reason
        req.resolved_at = datetime.now(timezone.utc)
        await db.commit()
        
        await self.log_execution(db, user_id, req.tool_name, {"approval_request_id": str(req.id)}, ToolResult(success=False, data="Approval Denied"), 0, event_type="approval_denied")
        return ApprovalRequest(
            id=req.id, user_id=req.user_id, tool_name=req.tool_name, 
            tool_input=req.tool_input, reason=req.reason, status=req.status
        )

    async def get_pending_approvals(self, db: AsyncSession, user_id: UUID) -> List[ApprovalRequest]:
        stmt = select(ApprovalRequestModel).where(
            and_(
                ApprovalRequestModel.user_id == user_id,
                ApprovalRequestModel.status == "pending"
            )
        )
        res = await db.execute(stmt)
        reqs = res.scalars().all()
        return [
            ApprovalRequest(id=r.id, user_id=r.user_id, tool_name=r.tool_name, tool_input=r.tool_input, reason=r.reason, status=r.status)
            for r in reqs
        ]

    async def grant_permission(self, db: AsyncSession, user_id: UUID, tool_name: str, permission_level: str, risk_level: str) -> None:
        stmt = select(ToolPermission).where(
            and_(
                ToolPermission.user_id == user_id,
                ToolPermission.tool_name == tool_name
            )
        )
        result = await db.execute(stmt)
        perm = result.scalar_one_or_none()
        
        if perm:
            perm.is_allowed = True
            perm.permission_level = permission_level
            perm.risk_level = risk_level
            perm.requires_approval = False # Approved directly
            perm.approved_at = datetime.now(timezone.utc)
            await db.commit()
        else:
            perm = ToolPermission(
                user_id=user_id,
                tool_name=tool_name,
                permission_level=permission_level,
                risk_level=risk_level,
                is_allowed=True,
                requires_approval=False,
                approved_at=datetime.now(timezone.utc)
            )
            db.add(perm)
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
                # Race condition caught by UniqueConstraint. Retry as update.
                stmt = update(ToolPermission).where(
                    and_(ToolPermission.user_id == user_id, ToolPermission.tool_name == tool_name)
                ).values(
                    is_allowed=True,
                    permission_level=permission_level,
                    risk_level=risk_level,
                    requires_approval=False,
                    approved_at=datetime.now(timezone.utc)
                )
                await db.execute(stmt)
                await db.commit()
                
        await self.log_execution(db, user_id, tool_name, {}, ToolResult(success=True, data="Granted"), 0, event_type="permission_granted")

    async def revoke_permission(self, db: AsyncSession, user_id: UUID, tool_name: str) -> None:
        stmt = select(ToolPermission).where(
            and_(
                ToolPermission.user_id == user_id,
                ToolPermission.tool_name == tool_name
            )
        )
        result = await db.execute(stmt)
        perm = result.scalar_one_or_none()
        if perm:
            perm.is_allowed = False
            perm.requires_approval = True
            await db.commit()
            await self.log_execution(db, user_id, tool_name, {}, ToolResult(success=True, data="Revoked"), 0, event_type="permission_revoked")

    async def log_execution(self, db: AsyncSession, user_id: UUID, tool_name: str, input_data: dict, result: ToolResult, duration_ms: int, event_type: str = "execution", approval_request_id: UUID = None) -> None:
        safe_input = _redact_input(input_data)
        log_entry = ExecutionLogModel(
            user_id=user_id,
            tool_name=tool_name,
            event_type=event_type,
            input_data=safe_input,
            success=result.success,
            duration_ms=duration_ms
        )
        # Fix #8: Record audit trail correlation
        if approval_request_id and hasattr(log_entry, "approval_request_id"):
            log_entry.approval_request_id = approval_request_id
            
        db.add(log_entry)
        await db.commit()

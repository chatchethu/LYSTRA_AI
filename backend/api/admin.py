from fastapi import APIRouter, Depends, HTTPException
from backend.auth.service import oauth2_scheme, AuthService

router = APIRouter(tags=["admin"])

# Dependency to verify superuser/admin status
async def get_current_admin_user(token: str = Depends(oauth2_scheme)):
    auth_service = AuthService()
    payload = auth_service.decode_token(token)
    
    # Check if 'admin' scope is present
    scopes = payload.get("scopes", [])
    if "admin" not in scopes:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return payload

@router.get("/api/v1/metrics/audit-logs")
async def view_audit_logs(admin: dict = Depends(get_current_admin_user)) -> list[dict]:
    # Replace with real DB call
    return [{"event": "mock_event", "admin": admin['sub']}]

@router.get("/api/v1/users")
async def list_users(admin: dict = Depends(get_current_admin_user)) -> list[dict]:
    # Replace with real DB call
    return [{"id": "user1", "email": "user1@example.com"}]

@router.get("/api/v1/metrics")
async def get_system_metrics(admin: dict = Depends(get_current_admin_user)) -> dict:
    # Gather exported metrics or system health
    return {"status": "ok", "active_tasks": 5}

@router.get("/api/v1/agent/tasks/admin")
async def list_all_tasks(admin: dict = Depends(get_current_admin_user)) -> list[dict]:
    # List all running background tasks across system
    return []

@router.post("/api/v1/users/{id}/deactivate")
async def deactivate_user(id: str, admin: dict = Depends(get_current_admin_user)) -> dict:
    # Update DB to deactivate user
    return {"status": "success", "user_id": id}

@router.get("/api/v1/metrics/evaluation/run")
async def run_evaluation_suite(admin: dict = Depends(get_current_admin_user)) -> dict:
    from backend.evaluation.evaluator import AgentEvaluator
    from backend.evaluation.test_runner import TestRunner
    
    runner = TestRunner(AgentEvaluator(), None)
    results = await runner.run_all()
    return results

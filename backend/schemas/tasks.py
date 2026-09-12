from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class PlanStep(BaseModel):
    """Phase 95: Visible Agent Plans"""
    id: str
    description: str
    status: str = Field(default="pending", description="pending, in_progress, completed, failed")
    
class TaskCapability(BaseModel):
    """Phase 93: Capability-based Security"""
    name: str

class AgentTask(BaseModel):
    id: str
    title: str
    capabilities: List[str] = []
    visible_steps: List[PlanStep] = []
    status: str
    created_at: datetime
    
class ApprovalRequest(BaseModel):
    """Phase 94: Human-in-the-Loop Center"""
    id: str
    task_id: str
    tool_name: str
    arguments: dict
    reason: str
    status: str = "pending" # pending, approved, rejected, edited


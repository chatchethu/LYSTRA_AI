from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class PlanStep(BaseModel):
    step_id: str
    description: str
    tool_name: Optional[str] = None
    status: str = "pending" # pending, in_progress, completed, failed
    result: Optional[str] = None

class AgentPlan(BaseModel):
    plan_id: str
    goal: str
    steps: List[PlanStep] = Field(default_factory=list)
    status: str = "created"

class TaskState(BaseModel):
    task_id: UUID
    user_id: UUID
    conversation_id: UUID
    goal: str
    plan: Optional[AgentPlan] = None
    status: str = "active"
    created_at: datetime
    updated_at: datetime

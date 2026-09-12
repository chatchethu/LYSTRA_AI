import re

with open("backend/tasks/manager.py", "r") as f:
    content = f.read()

load_plan_code = """
    async def load_plan(self, task_id: uuid.UUID) -> Optional[Plan]:
        \"\"\"Reconstruct a Plan object from the Task and TaskStep records in PostgreSQL.\"\"\"
        task = await self.get_task(task_id)
        if not task:
            return None
            
        stmt = select(TaskStep).where(TaskStep.task_id == task_id).order_by(TaskStep.step_index.asc())
        result = await self.db.execute(stmt)
        steps_db = result.scalars().all()
        
        from backend.agent.planner import PlanStep
        
        plan_steps = []
        for s in steps_db:
            plan_steps.append(PlanStep(
                id=s.name,
                title=s.details.get("title", ""),
                description=s.details.get("description", ""),
                tool_name=s.details.get("tool_name"),
                tool_input=s.details.get("tool_input"),
                depends_on=s.details.get("depends_on", []),
                risk_level=s.details.get("risk_level", "low"),
                status=s.status,
                result=s.details.get("result"),
                error=s.details.get("error")
            ))
            
        return Plan(
            id=task_id,
            goal=task.goal,
            steps=plan_steps,
            estimated_duration=None,
            requires_approval=False,
            created_at=task.created_at or datetime.utcnow(),
            max_steps=10
        )
"""

content = content.replace("    async def update_task(", load_plan_code + "\n    async def update_task(")

with open("backend/tasks/manager.py", "w") as f:
    f.write(content)

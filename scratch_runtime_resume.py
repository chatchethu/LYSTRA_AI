import re

with open("backend/agent/runtime.py", "r") as f:
    content = f.read()

# Add import
import_str = """from backend.agent.budget import ExecutionBudget, BudgetExceededError
from backend.tasks.manager import TaskStatus"""

content = content.replace("from backend.agent.replanner import Replanner", "from backend.agent.replanner import Replanner\n" + import_str)

resume_method = """
    async def resume_task(self, task_id: UUID, worker_id: str, context_dict: dict, stream_callback=None):
        \"\"\"Resume a task from PostgreSQL using its TaskStep records (Phase 18).\"\"\"
        budget = ExecutionBudget()
        
        # Lock the task
        task = await self.task_manager.claim_task(task_id, worker_id)
        if not task:
            return # Someone else claimed it or it's done
            
        try:
            plan = await self.task_manager.load_plan(task_id)
            if not plan:
                await self.task_manager.fail(task_id, "Plan could not be loaded.", is_permanent=True)
                return
                
            # Run the loop
            plan = await self._execute_plan_loop(plan, task_id, context_dict, budget, stream_callback)
            
            # If all steps are complete
            if all(s.status == "completed" for s in plan.steps):
                await self.task_manager.complete(task_id, "Task completed successfully.")
            elif any(s.status == "failed" for s in plan.steps):
                # The task loop exited but has failures.
                await self.task_manager.fail(task_id, "Task execution failed.", is_permanent=False)
                
        except BudgetExceededError as e:
            await self.task_manager.fail(task_id, str(e), is_permanent=False)
        except Exception as e:
            await self.task_manager.fail(task_id, str(e), is_permanent=False)
        finally:
            await self.task_manager.release_task(task_id, worker_id)
"""

content = content.replace("    async def process_message(", resume_method + "\n    async def process_message(")

# Update `_execute_plan_loop` to use budget
execute_sig = "async def _execute_plan_loop(self, plan: Plan, task_id: UUID, context_dict: dict, budget: ExecutionBudget = None, stream_callback=None) -> Plan:"
content = re.sub(r"    async def _execute_plan_loop\(self, plan: Plan, task_id: UUID, context_dict: dict, stream_callback=None\) -> Plan:", execute_sig, content)

budget_consume = """
        if budget is None:
            budget = ExecutionBudget()
            
        max_retries = budget.max_retries
        while True:
            budget.consume_step()
"""
content = re.sub(r"        max_retries = 3\n        while True:", budget_consume, content)

with open("backend/agent/runtime.py", "w") as f:
    f.write(content)

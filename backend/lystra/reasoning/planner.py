from typing import List
import json
from pydantic import BaseModel

class SubTask(BaseModel):
    id: str
    description: str
    dependencies: List[str]
    status: str = "pending"

class ExecutionPlan(BaseModel):
    goal: str
    subtasks: List[SubTask]

class Planner:
    def __init__(self, llm_gateway):
        self.llm = llm_gateway

    async def decompose_request(self, goal: str, constraints: List[str]) -> ExecutionPlan:
        """
        Phase 10: Request Decomposition
        Splits complex tasks into execution subtasks.
        """
        prompt = f"Goal: {goal}\nConstraints: {constraints}"
        system = "You are LYSTRA's planning engine. Decompose this complex request into a logical step-by-step execution plan. Output only valid JSON matching this schema: {'goal': 'string', 'subtasks': [{'id': 'string', 'description': 'string', 'dependencies': ['string'], 'status': 'string'}]}"
        
        try:
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
            response_text = await self.llm.chat(messages, temperature=0.1)
            
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            
            subtasks = [SubTask(**st) for st in data.get("subtasks", [])]
            return ExecutionPlan(goal=data.get("goal", goal), subtasks=subtasks)
        except Exception:
            # Fallback
            return ExecutionPlan(
                goal=goal,
                subtasks=[SubTask(id="1", description=f"Execute {goal}", dependencies=[])]
            )

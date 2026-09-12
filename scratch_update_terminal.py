import re

with open("backend/tasks/manager.py", "r") as f:
    content = f.read()

# Update update_status
update_status_new = """    async def update_status(self, task_id: uuid.UUID, new_status: TaskStatus) -> Optional[Task]:
        task = await self.get_task(task_id)
        if not task:
            return None
            
        task.status = new_status.value
        
        if new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task.completed_at = datetime.utcnow()
            task.worker_id = None
            task.lease_expires_at = None
        elif new_status == TaskStatus.RUNNING and not task.started_at:
            task.started_at = datetime.utcnow()
            
        await self.db.commit()
        await self.db.refresh(task)
        return task"""

content = re.sub(r"    async def update_status\(.*?return task", update_status_new, content, flags=re.DOTALL)

# Update complete
complete_new = """    async def complete(self, task_id: uuid.UUID, result: str) -> Optional[Task]:
        task = await self.get_task(task_id)
        if not task:
            return None
        task.result = result
        task.status = TaskStatus.COMPLETED.value
        task.completed_at = datetime.utcnow()
        task.worker_id = None
        task.lease_expires_at = None
        await self.db.commit()
        await self.db.refresh(task)
        return task"""

content = re.sub(r"    async def complete\(.*?return task", complete_new, content, flags=re.DOTALL)

with open("backend/tasks/manager.py", "w") as f:
    f.write(content)

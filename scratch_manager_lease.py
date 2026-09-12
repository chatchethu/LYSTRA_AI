import re

with open("backend/tasks/manager.py", "r") as f:
    content = f.read()

lease_methods = """
    async def claim_task(self, task_id: uuid.UUID, worker_id: str, lease_duration_seconds: int = 60) -> Optional[Task]:
        \"\"\"Attempts to claim a task exclusively using row-level locking.\"\"\"
        from datetime import timedelta
        
        stmt = select(Task).where(
            Task.id == task_id,
            Task.status.in_([TaskStatus.QUEUED.value, TaskStatus.RETRYING.value, TaskStatus.RUNNING.value, TaskStatus.WORKER_LOST.value])
        ).with_for_update(skip_locked=True)
        
        result = await self.db.execute(stmt)
        task = result.scalars().first()
        
        if not task:
            return None
            
        # Check if already locked by someone else
        if task.worker_id and task.worker_id != worker_id and task.lease_expires_at:
            if task.lease_expires_at > datetime.utcnow():
                # Lease is still valid for another worker
                return None
                
        # Claim it
        task.worker_id = worker_id
        task.lease_expires_at = datetime.utcnow() + timedelta(seconds=lease_duration_seconds)
        if task.status != TaskStatus.RUNNING.value:
            task.status = TaskStatus.RUNNING.value
            if not task.started_at:
                task.started_at = datetime.utcnow()
                
        await self.db.commit()
        await self.db.refresh(task)
        return task
        
    async def extend_lease(self, task_id: uuid.UUID, worker_id: str, lease_duration_seconds: int = 60) -> bool:
        \"\"\"Extends the lease for the current worker.\"\"\"
        from datetime import timedelta
        task = await self.get_task(task_id)
        if not task or task.worker_id != worker_id:
            return False
            
        task.lease_expires_at = datetime.utcnow() + timedelta(seconds=lease_duration_seconds)
        await self.db.commit()
        return True
        
    async def release_task(self, task_id: uuid.UUID, worker_id: str):
        task = await self.get_task(task_id)
        if task and task.worker_id == worker_id:
            task.worker_id = None
            task.lease_expires_at = None
            await self.db.commit()
"""

content = content.replace("    async def get_task(", lease_methods + "\n    async def get_task(")

fail_logic = """    async def fail(self, task_id: uuid.UUID, error: str, is_permanent: bool = False) -> Optional[Task]:
        task = await self.get_task(task_id)
        if not task:
            return None
            
        task.error = error
        task.worker_id = None
        task.lease_expires_at = None
        
        if not is_permanent and task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.RETRYING.value
        else:
            task.status = TaskStatus.FAILED.value
            task.completed_at = datetime.utcnow()
            
        await self.db.commit()
        await self.db.refresh(task)
        return task"""

content = re.sub(r"    async def fail\(.*?return task", fail_logic, content, flags=re.DOTALL)

with open("backend/tasks/manager.py", "w") as f:
    f.write(content)

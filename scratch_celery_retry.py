import re
with open("backend/workers/tasks.py", "r") as f:
    content = f.read()

replacement = """            # This handles Phase 18 (Real Executor flow), Phase 22 (Retry semantics) and Phase 23 (Execution Budget).
            await runtime.resume_task(task_uuid, worker_id, context)
            
            # Check if it needs celery retry
            async with AsyncSessionLocal() as check_db:
                check_manager = TaskManager(check_db)
                check_task = await check_manager.get_task(task_uuid)
                if check_task and check_task.status == TaskStatus.RETRYING.value:
                    raise Exception("Task needs retry")
                    
        finally:
            hb_task.cancel()"""

content = content.replace("            # This handles Phase 18 (Real Executor flow), Phase 22 (Retry semantics) and Phase 23 (Execution Budget).\n            await runtime.resume_task(task_uuid, worker_id, context)\n            \n        finally:\n            hb_task.cancel()", replacement)

with open("backend/workers/tasks.py", "w") as f:
    f.write(content)

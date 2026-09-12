import os

path = r'backend\api\admin.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('@router.get("/audit-logs")', '@router.get("/api/v1/metrics/audit-logs")')
content = content.replace('@router.get("/users")', '@router.get("/api/v1/users")')
content = content.replace('@router.post("/users/{id}/deactivate")', '@router.post("/api/v1/users/{id}/deactivate")')
content = content.replace('@router.get("/metrics")', '@router.get("/api/v1/metrics")')
content = content.replace('@router.get("/tasks")', '@router.get("/api/v1/agent/tasks/admin")')
content = content.replace('@router.get("/evaluation/run")', '@router.get("/api/v1/metrics/evaluation/run")')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

# We also need models and settings routers. Let's create them if they don't exist.
models_path = r'backend\api\models.py'
if not os.path.exists(models_path):
    with open(models_path, 'w', encoding='utf-8') as f:
        f.write('''from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/models", tags=["models"])

@router.get("")
async def get_models():
    return {"models": []}
''')

settings_path = r'backend\api\settings.py'
if not os.path.exists(settings_path):
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write('''from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

@router.get("")
async def get_settings():
    return {"settings": {}}
''')

# Include them in main.py
main_path = r'backend\main.py'
with open(main_path, 'r', encoding='utf-8') as f:
    main_content = f.read()

if "from backend.api import models" not in main_content:
    main_content = main_content.replace('from backend.api import messages, auth, conversations, memories, tasks', 'from backend.api import messages, auth, conversations, memories, tasks, models, settings')
    main_content = main_content.replace('app.include_router(tasks.schedule_router)', 'app.include_router(tasks.schedule_router)\\napp.include_router(models.router)\\napp.include_router(settings.router)')
    
with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main_content)

print("done")

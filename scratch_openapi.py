import os
os.environ["SECRET_KEY"] = "mock"
os.environ["REDIS_URL"] = "redis://mock:6379/0"
os.environ["CELERY_BROKER_URL"] = "redis://mock:6379/1"
os.environ["CELERY_RESULT_BACKEND"] = "redis://mock:6379/2"
os.environ["JWT_SECRET_KEY"] = "mock"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://mock:mock@localhost:5432/mock"
from backend.main import app
import json
import os

if not os.path.exists("docs"):
    os.makedirs("docs")
with open("docs/openapi.json", "w", encoding="utf-8") as f:
    f.write(json.dumps(app.openapi()))
print("openapi.json generated")

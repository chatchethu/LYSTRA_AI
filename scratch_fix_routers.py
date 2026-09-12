import os
import re

api_dir = r"backend\api"

# Fix tasks.py
tasks_path = os.path.join(api_dir, "tasks.py")
with open(tasks_path, "r", encoding="utf-8") as f:
    content = f.read()
content = content.replace('prefix="/api/v1/tasks"', 'prefix="/api/v1/agent/tasks"')
content = content.replace('prefix="/api/v1/scheduled"', 'prefix="/api/v1/agent/tasks/scheduled"')
with open(tasks_path, "w", encoding="utf-8") as f:
    f.write(content)

# Fix messages.py
messages_path = os.path.join(api_dir, "messages.py")
with open(messages_path, "r", encoding="utf-8") as f:
    content = f.read()
# We'll split the router into messages and chat_stream in main.py, or just use one router for messages but what about /api/v1/chat/stream?
# The easiest way is to let messages.py have two routers: router (for /messages) and stream_router (for /chat/stream).
# Or we can just mount messages_router with no prefix, and prefix the routes.

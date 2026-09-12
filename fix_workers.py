with open('backend/workers/tasks.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('from backend.tasks.manager import TaskManager, TaskStatus\n', '')

with open('backend/workers/tasks.py', 'w', encoding='utf-8') as f:
    f.write(content)

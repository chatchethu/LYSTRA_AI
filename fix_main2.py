with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('app.include_router(tasks.router)\n', '')
content = content.replace('app.include_router(tasks.schedule_router)\n', '')

with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

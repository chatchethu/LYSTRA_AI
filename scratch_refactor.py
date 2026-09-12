import os
import re

tools_dir = 'backend/tools'
files = []
for root, _, fs in os.walk(tools_dir):
    for f in fs:
        if f.endswith('.py') and f not in ('__init__.py', 'registry.py', 'executor.py', 'permissions.py', 'tool_router.py'):
            files.append(os.path.join(root, f))

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Remove second user_id
    content = re.sub(r',\s*user_id:\s*str\s*=\s*["\']default["\']', '', content)
    content = re.sub(r',\s*user_id\s*=\s*["\']default["\']', '', content)
    
    with open(f, 'w', encoding='utf-8') as file:
        file.write(content)

print("Fixed syntax.")

with open('backend/lystra/orchestration/execution_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_prompt = '''        system_policy = f"""[SYSTEM]
You are LYSTRA.
Current System Time: {current_time}

[POLICY]'''

new_prompt = '''        system_policy = f"""[SYSTEM]
You are LYSTRA.
Current System Time: {current_time}

[PRIORITY HIERARCHY]
You MUST enforce this strict priority hierarchy:
1. System/security policy (Highest)
2. Current explicit user request
3. Current task state
4. Current conversation context
5. Explicit user preferences
6. Relevant long-term memory
7. Weak/inferred preferences (Lowest)

[POLICY]'''

content = content.replace(old_prompt, new_prompt)

with open('backend/lystra/orchestration/execution_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Injected Priority Hierarchy")

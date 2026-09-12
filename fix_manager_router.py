with open('backend/lystra/orchestration/execution_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_call = '''tool_decision = await self.tool_router.route(user_message, understanding)'''
new_call = '''tool_decision = await self.tool_router.route(user_message, understanding, chat_history)'''

content = content.replace(old_call, new_call)

with open('backend/lystra/orchestration/execution_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated ExecutionManager to pass history to tool_router")

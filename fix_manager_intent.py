with open('backend/lystra/orchestration/execution_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_call = '''        # 6.5 Memory Wiring
        try:
            asyncio.create_task(self.memory_manager.process_user_message(str(user_id), user_message, [m["content"] for m in chat_history[-5:]]))'''

new_call = '''        # 6.5 Memory Wiring
        try:
            intent_val = understanding.intent.primary if hasattr(understanding, 'intent') and hasattr(understanding.intent, 'primary') else "conversation"
            asyncio.create_task(self.memory_manager.process_user_message(
                str(user_id), 
                user_message, 
                [m["content"] for m in chat_history[-5:]],
                intent=intent_val
            ))'''

content = content.replace(old_call, new_call)

with open('backend/lystra/orchestration/execution_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Passed intent to MemoryManager")

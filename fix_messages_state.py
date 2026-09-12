with open('backend/api/messages.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Add the import
content = content.replace(
    'from backend.schemas.message import MessageCreate\n',
    'from backend.schemas.message import MessageCreate\nfrom backend.lystra.context.conversation_state import ConversationState\n'
)

with open('backend/api/messages.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added ConversationState import")

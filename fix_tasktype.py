with open('backend/llm/model_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_enum = '''class TaskType(str, Enum):
    CHAT = "chat"
    CODE = "code"
    VISION = "vision"
    EMBEDDING = "embedding"
    PLANNING = "planning"
    RESEARCH = "research"
    CREATIVE = "creative"
    ROUTING = "routing"
    DOCUMENT = "document"'''

new_enum = '''class TaskType(str, Enum):
    CHAT = "chat"
    CODE = "code"
    VISION = "vision"
    EMBEDDING = "embedding"
    PLANNING = "planning"
    RESEARCH = "research"
    CREATIVE = "creative"
    ROUTING = "routing"
    DOCUMENT = "document"
    EXTRACTION = "extraction"'''

content = content.replace(old_enum, new_enum)

with open('backend/llm/model_router.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("TaskType.EXTRACTION added")

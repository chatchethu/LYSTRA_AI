with open('backend/api/messages.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('from backend.memory.service import MemoryService\n', '')

with open('backend/api/messages.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Removed legacy MemoryService import from messages.py")

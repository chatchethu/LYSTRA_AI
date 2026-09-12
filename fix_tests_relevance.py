with open('backend/tests/test_lystra_memory.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_r1 = 'mem1 = MemoryObject(user_id="1", type=MemoryType.COMMUNICATION, key="k1", value="React dev")'
new_r1 = 'mem1 = MemoryObject(user_id="1", type=MemoryType.COMMUNICATION, key="k1", value="React dev", importance=0.8, confidence=0.8, source=MemorySource.INFERRED)'
old_r2 = 'mem2 = MemoryObject(user_id="1", type=MemoryType.COMMUNICATION, key="k2", value="Travels", importance=0.1, confidence=0.1)'
new_r2 = 'mem2 = MemoryObject(user_id="1", type=MemoryType.COMMUNICATION, key="k2", value="Travels", importance=0.1, confidence=0.1, source=MemorySource.INFERRED)'

content = content.replace(old_r1, new_r1)
content = content.replace(old_r2, new_r2)

with open('backend/tests/test_lystra_memory.py', 'w', encoding='utf-8') as f:
    f.write(content)

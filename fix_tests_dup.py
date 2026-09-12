with open('backend/tests/test_lystra_memory.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(', importance=0.8, confidence=0.8)', ')')

with open('backend/tests/test_lystra_memory.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('backend/lystra/memory/memory_extractor.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('            confidence=confidence,\n            importance=classification.get("importance", 0.5),\n            source=source', '            confidence=confidence,\n            source=source')

with open('backend/lystra/memory/memory_extractor.py', 'w', encoding='utf-8') as f:
    f.write(content)

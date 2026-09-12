with open('backend/config.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

content = content.replace('SEMANTIC_ANALYSIS_TIMEOUT_S: float = 20.0', 'SEMANTIC_ANALYSIS_TIMEOUT_S: float = 120.0')

with open('backend/config.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('backend/lystra/understanding/semantic_analyzer.py', 'r', encoding='utf-8') as f:
    content2 = f.read()

content2 = content2.replace('retries = 2', 'retries = 1')

with open('backend/lystra/understanding/semantic_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(content2)

print("Fixed config and semantic_analyzer timeouts")

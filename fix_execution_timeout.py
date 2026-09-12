with open('backend/lystra/orchestration/execution_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_timeout = '''WEB_SEARCH_TIMEOUT_SECONDS = 20'''
new_timeout = '''WEB_SEARCH_TIMEOUT_SECONDS = 45'''

content = content.replace(old_timeout, new_timeout)

with open('backend/lystra/orchestration/execution_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Execution timeout increased to 45s.")

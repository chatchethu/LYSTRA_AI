import os

# fix errors.py
with open('backend/api/errors.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('NovaError', 'LystraError')
with open('backend/api/errors.py', 'w', encoding='utf-8') as f:
    f.write(content)

# fix main.py
with open('backend/main.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('NovaError', 'LystraError')
content = content.replace('nova_error_handler', 'lystra_error_handler')
with open('backend/main.py', 'w', encoding='utf-8') as f:
    f.write(content)

# fix code_execution.py
with open('backend/tools/code_execution.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('nova_sandbox_', 'lystra_sandbox_')
with open('backend/tools/code_execution.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Changed NovaError to LystraError everywhere.")

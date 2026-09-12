with open('backend/agent/runtime.py', 'r', encoding='utf-8') as f:
    text = f.read()
import re
text = re.sub(r'current_message=message \+ \(\".*?\n', 'current_message=message + ("\\n\\n" + doc_context if doc_context else ""), \n', text)
with open('backend/agent/runtime.py', 'w', encoding='utf-8') as f:
    f.write(text)

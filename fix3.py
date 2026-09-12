with open('backend/agent/runtime.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
new_lines = []
for line in lines:
    if "current_message=message +" in line:
        new_lines.append('                    current_message=message + ("\\n\\n" + doc_context if doc_context else ""), \n')
    else:
        new_lines.append(line)
with open('backend/agent/runtime.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

with open('backend/lystra/memory/memory_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_valid = '''                elif m.status == "active":
                    valid_mems.append(m)'''

new_valid = '''                elif m.status in ["active", "validated", "updated"]:
                    valid_mems.append(m)'''

content = content.replace(old_valid, new_valid)

with open('backend/lystra/memory/memory_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed status check")

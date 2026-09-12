with open('backend/lystra/memory/memory_updater.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_same = '''        # Fast filter by type
        same_type = [m for m in existing if m.type == candidate.type]
        if not same_type:
            return None'''

new_same = '''        # Fast filter by type
        same_type = existing if getattr(candidate, 'type', None) == 'any' else [m for m in existing if m.type == candidate.type]
        if not same_type:
            return None'''

content = content.replace(old_same, new_same)

with open('backend/lystra/memory/memory_updater.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed memory_updater.py for forget")

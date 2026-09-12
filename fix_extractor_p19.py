with open('backend/lystra/memory/memory_extractor.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_step1 = '''        persistence = classification.get("persistence", "none")
        if persistence == "none" and mem_type != MemoryType.TEMPORARY:
            return None'''

new_step1 = '''        persistence = classification.get("persistence", "none")
        if persistence == "none" and mem_type != MemoryType.TEMPORARY:
            return None

        # Phase 19: Prompt Injection Protection
        # Reject instruction-like content trying to manipulate system hierarchy
        injection_keywords = ["ignore", "system rules", "prompt", "instructions", "bypass", "forget everything"]
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in injection_keywords):
            # If it looks like an instruction override, DO NOT store it as a memory
            if "remember" in msg_lower or "always" in msg_lower:
                return None'''

content = content.replace(old_step1, new_step1)

with open('backend/lystra/memory/memory_extractor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added Phase 19 to memory_extractor.py")

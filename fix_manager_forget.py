with open('backend/lystra/memory/memory_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_process = '''        candidate = await self.extractor.extract_candidate_memory(user_id, message, context_history)
        if candidate:
            existing_memories = await self.storage.fetch_active_memories(user_id)'''

new_process = '''        # Phase 27: "Forget This" Semantics
        if "forget" in message.lower() or "do not remember" in message.lower():
            existing_memories = await self.storage.fetch_active_memories(user_id)
            conflict = await self.updater.find_semantic_conflict(
                candidate=type('obj', (object,), {'value': message, 'type': 'any'})(),
                existing=existing_memories, 
                llm=self.extractor.llm
            )
            if conflict:
                conflict.status = "deleted"
                await self.storage.update_memory(conflict)
                return

        candidate = await self.extractor.extract_candidate_memory(user_id, message, context_history)
        if candidate:
            existing_memories = await self.storage.fetch_active_memories(user_id)'''

content = content.replace(old_process, new_process)

with open('backend/lystra/memory/memory_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated memory_manager.py with forget semantics")

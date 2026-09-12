with open('backend/lystra/memory/memory_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_fetch = '''    async def fetch_active_memories(self, user_id):
        async with AsyncSessionLocal() as db:
            mems = await crud_memory.get_user_memories(db, user_id=uuid.UUID(str(user_id)))'''

new_fetch = '''    async def fetch_active_memories(self, user_id):
        async with AsyncSessionLocal() as db:
            mems = await crud_memory.get_user_memories(db, user_id=uuid.UUID(str(user_id)))
            
            # Phase 24: Memory Forgetting - Check Expiration
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            valid_mems = []
            for m in mems:
                if m.expires_at and m.expires_at.tzinfo is None:
                    # Make aware if naive
                    m.expires_at = m.expires_at.replace(tzinfo=timezone.utc)
                if m.expires_at and now > m.expires_at:
                    # Mark as expired in DB
                    m.status = "expired"
                    await db.commit()
                elif m.status == "active":
                    valid_mems.append(m)
            mems = valid_mems'''

content = content.replace(old_fetch, new_fetch)

with open('backend/lystra/memory/memory_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added expiration logic to DB fetch")

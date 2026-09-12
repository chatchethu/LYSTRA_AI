with open('backend/lystra/memory/memory_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# We will inject an audit logger helper into DBMemoryStorage
audit_helper = '''
    async def _audit(self, db, user_id, action, memory_id=None):
        """Phase 39: Audit Logging"""
        from backend.db.models.audit_log import AuditLog
        import uuid
        try:
            log = AuditLog(
                user_id=uuid.UUID(str(user_id)),
                action=action,
                resource_type="memory",
                resource_id=str(memory_id) if memory_id else None,
                details={"status": "success"} # DO NOT LOG SENSITIVE CONTENT
            )
            db.add(log)
            # We don't strictly await commit here, caller handles it.
        except Exception:
            pass
'''

old_update = '''    async def update_memory(self, memory):
        async with AsyncSessionLocal() as db:
            from backend.schemas.memory import MemoryCreate
            obj_in = MemoryCreate(
                user_id=uuid.UUID(str(memory.user_id)),
                memory_type=memory.type.value,
                content=str(memory.value),
                importance=memory.importance,
                confidence=memory.confidence
            )
            await crud_memory.create(db, obj_in=obj_in)
            await db.commit()'''

new_update = audit_helper + '''
    async def update_memory(self, memory):
        async with AsyncSessionLocal() as db:
            from backend.schemas.memory import MemoryCreate
            obj_in = MemoryCreate(
                user_id=uuid.UUID(str(memory.user_id)),
                memory_type=memory.type.value,
                content=str(memory.value),
                importance=memory.importance,
                confidence=memory.confidence
            )
            mem = await crud_memory.create(db, obj_in=obj_in)
            await self._audit(db, memory.user_id, "memory_updated", mem.id)
            await db.commit()
            
    async def deactivate_memory(self, memory):
        async with AsyncSessionLocal() as db:
            await self._audit(db, memory.user_id, "memory_deleted", memory.id)
            await db.commit()
'''

content = content.replace(old_update, new_update)

# Also update add_memory
old_add = '''    async def add_memory(self, memory):
        await self.update_memory(memory)'''
new_add = '''    async def add_memory(self, memory):
        async with AsyncSessionLocal() as db:
            from backend.schemas.memory import MemoryCreate
            obj_in = MemoryCreate(
                user_id=uuid.UUID(str(memory.user_id)),
                memory_type=memory.type.value,
                content=str(memory.value),
                importance=memory.importance,
                confidence=memory.confidence
            )
            mem = await crud_memory.create(db, obj_in=obj_in)
            await self._audit(db, memory.user_id, "memory_created", mem.id)
            await db.commit()'''

content = content.replace(old_add, new_add)

with open('backend/lystra/memory/memory_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Added audit logging to DBMemoryStorage")

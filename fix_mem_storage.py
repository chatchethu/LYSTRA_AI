with open('backend/lystra/memory/memory_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

db_mock = '''class MemoryStorageMock:
    # A simple mock since we haven't implemented DB layer yet
    def __init__(self):
        self.memories = []
    async def fetch_active_memories(self, user_id):
        return self.memories
    async def update_memory(self, memory):
        pass'''

db_real = '''from backend.db.session import AsyncSessionLocal
from backend.crud.memory import memory as crud_memory
import uuid
import json

class DBMemoryStorage:
    async def fetch_active_memories(self, user_id):
        async with AsyncSessionLocal() as db:
            mems = await crud_memory.get_user_memories(db, user_id=uuid.UUID(str(user_id)))
            # Convert DB model to MemoryObject schema for compatibility
            from backend.lystra.memory.schemas import MemoryObject
            objs = []
            for m in mems:
                try:
                    obj = MemoryObject(
                        id=str(m.id),
                        user_id=str(m.user_id),
                        type=m.memory_type,
                        key=m.content[:50],  # Mock key
                        value=m.content,
                        confidence=m.confidence,
                        importance=m.importance,
                        source="user_explicit",
                        status="active"
                    )
                    objs.append(obj)
                except Exception as e:
                    pass
            return objs

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
            await crud_memory.create(db, obj_in=obj_in)
            await db.commit()

    async def add_memory(self, memory):
        await self.update_memory(memory)
'''

content = content.replace(db_mock, db_real)
content = content.replace('self.storage = MemoryStorageMock()', 'self.storage = DBMemoryStorage()')
content = content.replace('self.storage.memories.append(candidate) # Mock save', 'await self.storage.add_memory(candidate)')

with open('backend/lystra/memory/memory_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated memory_manager.py")

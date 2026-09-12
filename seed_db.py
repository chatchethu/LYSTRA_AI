import asyncio
import uuid
from backend.db.session import AsyncSessionLocal
from backend.schemas.memory import MemoryCreate
from backend.crud.memory import memory as crud_memory

async def main():
    async with AsyncSessionLocal() as db:
        user_id = uuid.UUID("20733854-fb5d-45e1-aec0-1b780e66fab0")
        obj_in = MemoryCreate(
            user_id=user_id,
            memory_type="identity",
            content="My name is Rahul, I am an AI enthusiast.",
            importance=0.95,
            confidence=0.90
        )
        await crud_memory.create(db, obj_in=obj_in)
        
        obj_in2 = MemoryCreate(
            user_id=user_id,
            memory_type="communication",
            content="I prefer highly concise and direct responses. Do not use overly long paragraphs.",
            importance=0.85,
            confidence=0.95
        )
        await crud_memory.create(db, obj_in=obj_in2)
        await db.commit()
        print("Seeded test memories")

asyncio.run(main())

import asyncio
from backend.db.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("SELECT id, user_id, memory_type, content, status FROM memories"))
        for row in result:
            print(f"Memory: {row.id} | User: {row.user_id} | Type: {row.memory_type} | Content: {row.content} | Status: {row.status}")

asyncio.run(main())

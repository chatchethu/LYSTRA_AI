import asyncio
from backend.db.session import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        # Delete useless greeting and empty memories
        await db.execute(text("DELETE FROM memories WHERE memory_type = 'greeting' OR content IN ('hi', 'hello', 'ok', 'What is my name?', 'who are you', 'I told you earlier.', 'whones you', 'who trained you')"))
        await db.commit()
        print("Cleaned up useless memories")

asyncio.run(main())

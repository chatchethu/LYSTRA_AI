import asyncio
from uuid import UUID
from backend.db.session import AsyncSessionLocal
from backend.crud.conversation import conversation as crud_conversation

async def check():
    async with AsyncSessionLocal() as db:
        cid = UUID("b4d0a030-23c7-4f00-a644-8fcbdf8aa846")
        try:
            conv = await crud_conversation.get(db, id=cid)
            print("Loaded conversation:", conv.title if conv else "None")
        except Exception as e:
            print("Error loading conversation:")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check())

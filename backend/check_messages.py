import asyncio
from uuid import UUID
from backend.db.session import get_db
from backend.crud.message import message as crud_message
from backend.schemas.message import MessageResponse

async def check_messages():
    async for db in get_db():
        cid = UUID("b4d0a030-23c7-4f00-a644-8fcbdf8aa846")
        msgs = await crud_message.get_conversation_messages(db, conversation_id=cid)
        print(f"Found {len(msgs)} messages.")
        for msg in msgs:
            try:
                MessageResponse.model_validate(msg)
            except Exception as e:
                print(f"Validation error on message {msg.id}:")
                print(e)
                print(f"Raw metadata_: {msg.metadata_}")
        break

if __name__ == "__main__":
    asyncio.run(check_messages())

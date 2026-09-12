import asyncio
from uuid import UUID
from backend.db.session import AsyncSessionLocal
from backend.crud.message import message as crud_message
from backend.schemas.message import MessageResponse
from fastapi.encoders import jsonable_encoder

async def check_messages():
    async with AsyncSessionLocal() as db:
        cid = UUID("b4d0a030-23c7-4f00-a644-8fcbdf8aa846")
        msgs = await crud_message.get_conversation_messages(db, conversation_id=cid)
        print(f"Found {len(msgs)} messages.")
        for msg in msgs:
            try:
                validated = MessageResponse.model_validate(msg)
                encoded = jsonable_encoder(validated)
                print(f"Encoded msg {msg.id} OK.")
            except Exception as e:
                print(f"Error on message {msg.id}:")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_messages())

import asyncio
import httpx
import json

async def test_stream():
    url = "http://localhost:8000/api/v1/chat/stream"
    headers = {"Content-Type": "application/json"}
    payload = {
        "message": "Hello, how are you?",
        "conversation_id": None,
        "stream": True
    }
    
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", url, json=payload, headers=headers) as response:
            print(f"Status: {response.status_code}")
            async for chunk in response.aiter_text():
                print(f"CHUNK: {chunk!r}")

asyncio.run(test_stream())

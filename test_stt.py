import asyncio
from backend.multimodal.stt import SpeechToText
import os

os.environ["SARVAM_API_KEY"] = "mock-key"
os.environ["SARVAM_STT_URL"] = "https://httpbin.org/post"

async def test():
    stt = SpeechToText()
    audio = b"fakeaudio"
    try:
        res = await stt.transcribe_bytes(audio)
        print("Success:", res)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())

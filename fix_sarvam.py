with open('backend/config.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_sarvam = '''    SARVAM_API_KEY: Optional[str] = None
    SARVAM_STT_MODEL: str = "saaras:v3"'''

new_sarvam = '''    SARVAM_API_KEY: Optional[str] = None
    SARVAM_API_KEYS: list[str] = [] # Supports rotation
    SARVAM_STT_MODEL: str = "saaras:v3"'''

content = content.replace(old_sarvam, new_sarvam)

with open('backend/config.py', 'w', encoding='utf-8') as f:
    f.write(content)

with open('backend/multimodal/stt.py', 'r', encoding='utf-8') as f:
    stt_content = f.read()

old_stt = '''        settings = get_settings()
        if not settings.SARVAM_API_KEY:
            raise RuntimeError("Speech-to-text is not configured. Set SARVAM_API_KEY on the backend.")'''

new_stt = '''        settings = get_settings()
        import random
        keys = []
        if settings.SARVAM_API_KEYS:
            keys.extend(settings.SARVAM_API_KEYS)
        if settings.SARVAM_API_KEY:
            keys.append(settings.SARVAM_API_KEY)
            
        if not keys:
            raise RuntimeError("Speech-to-text is not configured. Set SARVAM_API_KEY or SARVAM_API_KEYS on the backend.")
            
        api_key = random.choice(keys)'''

stt_content = stt_content.replace(old_stt, new_stt)

old_stt_req = '''        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                settings.SARVAM_STT_URL,
                headers={"API-Subscription-Key": settings.SARVAM_API_KEY},'''

new_stt_req = '''        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                settings.SARVAM_STT_URL,
                headers={"API-Subscription-Key": api_key},'''

stt_content = stt_content.replace(old_stt_req, new_stt_req)

with open('backend/multimodal/stt.py', 'w', encoding='utf-8') as f:
    f.write(stt_content)
print("Sarvam API rotation fixed")

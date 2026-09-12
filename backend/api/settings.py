from fastapi import APIRouter, Request
router = APIRouter(prefix="/api/v1/settings", tags=["settings"])

_MOCK_SETTINGS = {
    "default_model": "gpt-4-turbo",
    "temperature": 0.7,
    "personality": "helpful",
    "response_style": "balanced",
    "language": "en",
    "proactivity_level": "medium",
    "verbosity": 2
}

@router.get("")
async def get_settings():
    return {"settings": _MOCK_SETTINGS}

@router.post("")
async def update_settings(request: Request):
    global _MOCK_SETTINGS
    data = await request.json()
    _MOCK_SETTINGS.update(data)
    return {"settings": _MOCK_SETTINGS}

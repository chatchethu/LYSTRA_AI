from fastapi import APIRouter
router = APIRouter(prefix="/api/v1/models", tags=["models"])

@router.get("")
async def get_models():
    return {"models": []}

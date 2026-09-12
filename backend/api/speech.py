from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel

from backend.auth.dependencies import get_optional_current_user
from backend.db.models.user import User
from backend.multimodal.stt import SpeechToText
from backend.api.rate_limit import MultiRateLimit, user_rate_limit, file_upload_limit

router = APIRouter(
    prefix="/api/v1/speech",
    tags=["speech"],
    dependencies=[Depends(MultiRateLimit(user_rate_limit, file_upload_limit))],
)
stt = SpeechToText()

MAX_AUDIO_BYTES = 25 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {
    "audio/wav", "audio/x-wav", "audio/webm", "audio/ogg", "audio/mp4",
    "audio/mpeg", "audio/flac", "audio/aac", "application/octet-stream",
}


class TranscriptionResponse(BaseModel):
    text: str
    language: str
    confidence: float


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(...),
    _current_user: User = Depends(get_optional_current_user),
):
    if file.content_type and file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported audio format.")

    audio_data = await file.read(MAX_AUDIO_BYTES + 1)
    if len(audio_data) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio recording is too large.")

    filename = file.filename or "recording.wav"
    extension = filename.rsplit(".", 1)[-1] if "." in filename else "wav"
    try:
        result = await stt.transcribe_bytes(audio_data, extension)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return TranscriptionResponse(text=result.text, language=result.language, confidence=result.confidence)
import os
import asyncio
import httpx
import json
from typing import AsyncGenerator
from pydantic import BaseModel
from backend.config import get_settings

class TranscriptionResult(BaseModel):
    text: str
    language: str
    confidence: float
    segments: list[dict]
    duration_seconds: float

class SpeechToText:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    async def transcribe_bytes(self, audio_data: bytes, format: str = "wav") -> TranscriptionResult:
        settings = get_settings()
        import random
        keys = []
        if settings.SARVAM_API_KEYS:
            keys.extend(settings.SARVAM_API_KEYS)
        if settings.SARVAM_API_KEY:
            keys.append(settings.SARVAM_API_KEY)
            
        if not keys:
            raise RuntimeError("Speech-to-text is not configured. Set SARVAM_API_KEY or SARVAM_API_KEYS on the backend.")
            
        api_key = random.choice(keys)
        if not audio_data:
            raise ValueError("The audio recording is empty.")

        extension = format.lower().lstrip(".") or "wav"
        content_types = {
            "wav": "audio/wav", "webm": "audio/webm", "ogg": "audio/ogg",
            "mp4": "audio/mp4", "m4a": "audio/mp4", "mp3": "audio/mpeg", "flac": "audio/flac",
        }
        
        # Sometimes WebM comes through with OGG or MKV headers, making sure we have standard content type
        files = {"file": (f"recording.{extension}", audio_data, content_types.get(extension, "application/octet-stream"))}
        data = {
            "model": settings.SARVAM_STT_MODEL,
        }
        
        # Some Sarvam models require language_code or other fields
        # If SARVAM_STT_MODE is set in settings, pass it, otherwise assume transcribe
        if hasattr(settings, "SARVAM_STT_MODE") and settings.SARVAM_STT_MODE:
            data["mode"] = settings.SARVAM_STT_MODE
            
        # Add language_code as many Sarvam models strictly require it
        # Try defaulting to "en-IN" if not explicitly specified elsewhere
        data["language_code"] = "en-IN"

        headers = {"api-subscription-key": settings.SARVAM_API_KEY}

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                response = await client.post(settings.SARVAM_STT_URL, headers=headers, data=data, files=files)
        except httpx.RequestError as exc:
            raise RuntimeError(f"Could not reach the speech-to-text service: {str(exc)}") from exc

        if response.is_error:
            detail = f"Speech-to-text service rejected the recording (Status {response.status_code})."
            try:
                payload = response.json()
                # Handle Sarvam's specific error object format: {"error": {"message": "..."}}
                if "error" in payload and isinstance(payload["error"], dict):
                    detail = payload["error"].get("message") or str(payload["error"])
                else:
                    detail = payload.get("detail") or payload.get("message") or payload.get("error") or detail
                    if isinstance(detail, dict):
                        detail = str(detail)
            except ValueError:
                detail += f" Raw: {response.text[:200]}"
            raise RuntimeError(str(detail))

        try:
            payload = response.json()
        except ValueError:
            raise RuntimeError(f"Speech-to-text returned invalid JSON: {response.text[:200]}")

        # Handle different response formats based on the API version
        text = payload.get("transcript") or payload.get("text") or ""
        
        # If it returns a list of results (translation API)
        if not text and isinstance(payload.get("results"), list) and len(payload["results"]) > 0:
            text = payload["results"][0].get("transcript") or payload["results"][0].get("text") or ""

        if not isinstance(text, str) or not text.strip():
            raise RuntimeError(f"Speech-to-text returned no transcript. Payload: {json.dumps(payload)[:200]}")

        return TranscriptionResult(
            text=text.strip(),
            language=payload.get("language_code") or payload.get("language") or "en",
            confidence=float(payload.get("confidence") or 0.99),
            segments=payload.get("segments") or [],
            duration_seconds=float(payload.get("duration_seconds") or 0),
        )
        
    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        return self._model

    async def transcribe_file(self, audio_path: str, language: str = None) -> TranscriptionResult:
        model = self._get_model()
        loop = asyncio.get_running_loop()
        
        segments_gen, info = await loop.run_in_executor(None, lambda: model.transcribe(audio_path, language=language))
        
        segments = []
        full_text = ""
        def process_segments():
            nonlocal full_text
            for segment in segments_gen:
                segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                })
                full_text += segment.text + " "
                
        await loop.run_in_executor(None, process_segments)
        
        return TranscriptionResult(
            text=full_text.strip(),
            language=info.language,
            confidence=info.language_probability,
            segments=segments,
            duration_seconds=segments[-1]["end"] if segments else 0
        )

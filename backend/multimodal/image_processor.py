"""
Image Processor — LYSTRA Multimodal V1

Sends images to a vision-capable LLM (qwen2.5vl:3b) via Ollama.
Gracefully degrades if the vision model is not available.
"""
from __future__ import annotations
import base64
import io
from typing import TYPE_CHECKING

try:
    from PIL import Image as PILImage
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

from backend.multimodal.file_context import FileContext, FileChunk, FileType, FileStatus

if TYPE_CHECKING:
    from backend.llm.gateway import LLMGateway


_MAX_IMAGE_SIZE = (1280, 1280)
_VISION_UNAVAILABLE_MSG = (
    "Image analysis requires a vision model (qwen2.5vl:3b). "
    "Please run: ollama pull qwen2.5vl:3b — then restart the server."
)


class ImageProcessor:
    """Analyzes images via Ollama vision LLM."""

    def __init__(self, llm: "LLMGateway | None" = None, vision_model: str = "qwen2.5vl:3b"):
        self.llm = llm
        self.vision_model = vision_model
        self._vision_available: bool | None = None  # cached check

    async def _check_vision_available(self) -> bool:
        """Check once whether the vision model is loaded in Ollama."""
        if self._vision_available is not None:
            return self._vision_available
        try:
            import httpx
            from backend.config import get_settings
            settings = get_settings()
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
                if resp.status_code == 200:
                    models = [m["name"] for m in resp.json().get("models", [])]
                    self._vision_available = self.vision_model in models
                    return self._vision_available
        except Exception:
            pass
        self._vision_available = False
        return False

    def _preprocess(self, image_bytes: bytes) -> tuple[bytes, str]:
        """Resize image to fit context window. Returns (bytes, mime_type)."""
        if not _PIL_OK:
            return image_bytes, "image/jpeg"
        try:
            img = PILImage.open(io.BytesIO(image_bytes))
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.thumbnail(_MAX_IMAGE_SIZE, PILImage.Resampling.LANCZOS)
            out = io.BytesIO()
            img.save(out, format="JPEG", quality=85)
            return out.getvalue(), "image/jpeg"
        except Exception:
            return image_bytes, "image/jpeg"

    async def process(self, file_id: str, filename: str, file_bytes: bytes) -> FileContext:
        # Check if vision model is available
        vision_ok = await self._check_vision_available()
        if not vision_ok:
            return FileContext(
                file_id=file_id, filename=filename, file_type=FileType.IMAGE,
                status=FileStatus.FAILED,
                error=_VISION_UNAVAILABLE_MSG
            )

        try:
            processed_bytes, _ = self._preprocess(file_bytes)
            b64 = base64.b64encode(processed_bytes).decode()

            # Ask the vision model for a structured analysis
            system_prompt = (
                "You are a vision analysis assistant. Analyze the provided image carefully. "
                "Describe: (1) what you see overall, (2) any visible text (verbatim), "
                "(3) notable UI elements if it's a screenshot, "
                "(4) any data/charts if present. Be thorough but concise."
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Analyze this image.",
                    "images": [b64]
                }
            ]
            analysis = await self.llm.chat(messages=messages, model=self.vision_model)

            chunk = FileChunk(
                chunk_type="visual_analysis",
                content=analysis,
                page=None
            )
            return FileContext(
                file_id=file_id, filename=filename, file_type=FileType.IMAGE,
                status=FileStatus.READY, chunks=[chunk]
            )

        except Exception as e:
            return FileContext(
                file_id=file_id, filename=filename, file_type=FileType.IMAGE,
                status=FileStatus.FAILED, error=str(e)
            )

    async def answer_question(self, file_bytes: bytes, question: str) -> str:
        """Ask a specific question about an image (used during Q&A, not just upload)."""
        vision_ok = await self._check_vision_available()
        if not vision_ok:
            return _VISION_UNAVAILABLE_MSG

        processed_bytes, _ = self._preprocess(file_bytes)
        b64 = base64.b64encode(processed_bytes).decode()
        messages = [
            {
                "role": "user",
                "content": (
                    f"User question about this image: {question}\n\n"
                    "Answer based only on what you can observe in the image. "
                    "Do not invent information."
                ),
                "images": [b64]
            }
        ]
        try:
            return await self.llm.chat(messages=messages, model=self.vision_model)
        except Exception as e:
            return f"Image analysis failed: {e}"

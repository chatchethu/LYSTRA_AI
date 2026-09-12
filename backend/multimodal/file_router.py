"""
File Router — LYSTRA Multimodal V1

Central file type detection and routing.
Validates MIME type + magic bytes. Never trusts filenames alone.
"""
from __future__ import annotations

from backend.multimodal.file_context import FileContext, FileType, FileStatus

# Allowed MIME types and their extensions
_ALLOWED = {
    # Images
    "image/jpeg": FileType.IMAGE,
    "image/jpg":  FileType.IMAGE,
    "image/png":  FileType.IMAGE,
    "image/webp": FileType.IMAGE,
    # PDF
    "application/pdf": FileType.PDF,
    # DOCX
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCUMENT,
    # DOC (legacy)
    "application/msword": FileType.DOCUMENT,
}

# Magic byte signatures for extra validation
_MAGIC_SIGNATURES: dict[bytes, str] = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG":      "image/png",
    b"RIFF":         "image/webp",    # simplified — webp starts with RIFF
    b"%PDF":         "application/pdf",
    b"PK\x03\x04":  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    b"\xd0\xcf\x11\xe0": "application/msword",  # legacy DOC
}

_ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".pdf", ".doc", ".docx"}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB


def detect_mime_from_bytes(file_bytes: bytes) -> str | None:
    """Detect MIME type from magic bytes. Returns None if unrecognized."""
    for magic, mime in _MAGIC_SIGNATURES.items():
        if file_bytes[:len(magic)] == magic:
            return mime
    return None


class FileRouter:
    """
    Validates uploads and routes them to the correct processor.
    Returns a FileContext ready for storage and Q&A.
    """

    def __init__(self, llm=None):
        from backend.config import get_settings
        settings = get_settings()
        vision_model = settings.OLLAMA_VISION_MODEL

        from backend.multimodal.image_processor import ImageProcessor
        from backend.multimodal.pdf_processor import PDFProcessor
        from backend.multimodal.doc_processor import DocProcessor

        self.image_processor = ImageProcessor(llm=llm, vision_model=vision_model)
        self.pdf_processor = PDFProcessor(llm=llm, vision_model=vision_model)
        self.doc_processor = DocProcessor(llm=llm, vision_model=vision_model)

    def validate(self, filename: str, content_type: str, file_bytes: bytes) -> tuple[bool, str]:
        """
        Returns (ok, error_message).
        Validates size, extension, and MIME from both header and magic bytes.
        """
        import os
        ext = os.path.splitext(filename)[1].lower()

        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            return False, f"File too large. Maximum size is 50 MB."

        if ext not in _ALLOWED_EXTENSIONS:
            return False, (
                f"File type '{ext}' is not supported. "
                "Allowed: JPG, PNG, WEBP, PDF, DOC, DOCX"
            )

        # Cross-check declared MIME vs magic bytes
        detected_mime = detect_mime_from_bytes(file_bytes)
        declared_ok = content_type in _ALLOWED
        detected_ok = detected_mime in _ALLOWED if detected_mime else True

        if not declared_ok and not detected_ok:
            return False, (
                f"Unsupported file type. Only images (JPG/PNG/WEBP), PDF, and Word documents are allowed."
            )

        return True, ""

    async def route(self, file_id: str, filename: str, content_type: str, file_bytes: bytes) -> FileContext:
        """
        Detect type and delegate to the correct processor.
        """
        # Prefer magic bytes detection over declared MIME
        detected_mime = detect_mime_from_bytes(file_bytes)
        effective_mime = detected_mime or content_type

        file_type = _ALLOWED.get(effective_mime)

        if file_type is None:
            return FileContext(
                file_id=file_id, filename=filename,
                file_type=FileType.IMAGE,  # placeholder
                status=FileStatus.FAILED,
                error="Unrecognized file type"
            )

        if file_type == FileType.IMAGE:
            print(f"[LYSTRA] Image processing started for {filename}")
            return await self.image_processor.process(file_id, filename, file_bytes)
        elif file_type == FileType.PDF:
            print(f"[LYSTRA] PDF processing started for {filename}")
            return await self.pdf_processor.process(file_id, filename, file_bytes)
        elif file_type == FileType.DOCUMENT:
            print(f"[LYSTRA] Document processing started for {filename}")
            return await self.doc_processor.process(file_id, filename, file_bytes)
        else:
            return FileContext(
                file_id=file_id, filename=filename, file_type=file_type,
                status=FileStatus.FAILED, error="No processor for this file type"
            )

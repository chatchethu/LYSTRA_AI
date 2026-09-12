"""
PDF Processor — LYSTRA Multimodal V1

Handles:
  - Native text PDFs (extract with pypdf)
  - Scanned/image PDFs (render pages → send to vision model)
"""
from __future__ import annotations
import io
from typing import TYPE_CHECKING

try:
    import pypdf
    _PYPDF_OK = True
except ImportError:
    _PYPDF_OK = False

try:
    _PIL_OK = True
except ImportError:
    _PIL_OK = False

from backend.multimodal.file_context import FileContext, FileChunk, FileType, FileStatus

if TYPE_CHECKING:
    from backend.llm.gateway import LLMGateway


_SCANNED_THRESHOLD = 30  # chars per page — below this = likely scanned


class PDFProcessor:
    """Extracts structured content from PDF files."""

    def __init__(self, llm: "LLMGateway | None" = None, vision_model: str = "qwen2.5vl:3b"):
        self.llm = llm
        self.vision_model = vision_model

    async def process(self, file_id: str, filename: str, file_bytes: bytes) -> FileContext:
        if not _PYPDF_OK:
            return FileContext(
                file_id=file_id, filename=filename, file_type=FileType.PDF,
                status=FileStatus.FAILED, error="pypdf not installed"
            )

        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            page_count = len(reader.pages)

            chunks: list[FileChunk] = []
            scanned_pages: list[tuple[int, bytes]] = []

            # --- Pass 1: Try text extraction ---
            for page_num, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                if len(text) >= _SCANNED_THRESHOLD:
                    # Good text content — chunk it
                    chunks.append(FileChunk(
                        chunk_type="text",
                        content=text,
                        page=page_num
                    ))
                else:
                    # Likely scanned — mark for vision pass
                    scanned_pages.append((page_num, b""))  # bytes filled below

            # --- Pass 2: OCR scanned pages via vision model ---
            if scanned_pages and self.llm:
                try:
                    import fitz  # PyMuPDF — optional
                    print("[LYSTRA] Rendering required pages via PyMuPDF")
                    doc = fitz.open(stream=file_bytes, filetype="pdf")
                    for page_num, _ in scanned_pages:
                        print(f"[LYSTRA] Sending page {page_num} to {self.vision_model}")
                        page = doc[page_num - 1]
                        pix = page.get_pixmap(dpi=150)
                        img_bytes = pix.tobytes("png")
                        vision_text = await self._ocr_image(img_bytes)
                        if vision_text:
                            print(f"[LYSTRA] Vision analysis for page {page_num}: SUCCESS")
                            chunks.append(FileChunk(
                                chunk_type="text",
                                content=f"[OCR] {vision_text}",
                                page=page_num
                            ))
                        else:
                            print(f"[LYSTRA] Vision analysis for page {page_num}: FAILED")
                    doc.close()
                except ImportError:
                    # PyMuPDF not available — skip scanned pages gracefully
                    for page_num, _ in scanned_pages:
                        chunks.append(FileChunk(
                            chunk_type="text",
                            content="[Scanned page — OCR requires PyMuPDF]",
                            page=page_num
                        ))

            # Sort by page
            chunks.sort(key=lambda c: c.page or 0)

            if not chunks:
                return FileContext(
                    file_id=file_id, filename=filename, file_type=FileType.PDF,
                    status=FileStatus.FAILED,
                    error="No readable content found in PDF"
                )

            return FileContext(
                file_id=file_id, filename=filename, file_type=FileType.PDF,
                status=FileStatus.READY, chunks=chunks, page_count=page_count
            )

        except Exception as e:
            return FileContext(
                file_id=file_id, filename=filename, file_type=FileType.PDF,
                status=FileStatus.FAILED, error=str(e)
            )

    async def _ocr_image(self, image_bytes: bytes) -> str:
        """Send image page to vision LLM for OCR."""
        import base64
        b64 = base64.b64encode(image_bytes).decode()
        messages = [{
            "role": "user",
            "content": (
                "You are LYSTRA's visual document analysis engine.\n\n"
                "Analyze the provided PDF page carefully.\n"
                "Extract:\n"
                "- visible text\n"
                "- headings\n"
                "- important facts\n"
                "- tables\n"
                "- charts\n"
                "- images\n"
                "- names\n"
                "- dates\n"
                "- numbers\n"
                "- relevant document structure\n\n"
                "Do not invent information. Return only information that can be supported by the provided page."
            ),
            "images": [b64]
        }]
        try:
            return await self.llm.chat(messages=messages, model=self.vision_model)
        except Exception:
            return ""

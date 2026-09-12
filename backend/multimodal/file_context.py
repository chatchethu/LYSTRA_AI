"""
Universal FileContext — LYSTRA Multimodal V1

A single data structure representing any analyzed file,
regardless of whether it was an image, PDF, or DOCX.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FileType(str, Enum):
    IMAGE = "image"
    PDF = "pdf"
    DOCUMENT = "document"


class FileStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


@dataclass
class FileChunk:
    """A single piece of content extracted from a file."""
    chunk_type: str          # "text" | "table" | "visual_analysis" | "heading"
    content: str
    page: int | None = None  # PDF/DOCX page number, None for images
    section: str | None = None  # DOCX heading context

    def to_prompt_block(self) -> str:
        parts = []
        if self.page is not None:
            parts.append(f"[Page {self.page}]")
        if self.section:
            parts.append(f"[Section: {self.section}]")
        parts.append(self.content)
        return " ".join(parts)


@dataclass
class FileContext:
    """
    Universal file context injected into the LLM prompt.
    Same structure for image, PDF, and DOCX files.
    """
    file_id: str
    filename: str
    file_type: FileType
    status: FileStatus
    chunks: list[FileChunk] = field(default_factory=list)
    page_count: int | None = None
    error: str | None = None
    disk_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_prompt_block(self, max_chars: int = 8000) -> str:
        """
        Render file content as an LLM-injectable prompt block.
        Truncates intelligently to stay within token budget.
        """
        if self.status == FileStatus.FAILED:
            return (
                f"=== FILE CONTEXT ===\n"
                f"File: {self.filename}\n"
                f"Status: PROCESSING FAILED — {self.error or 'unknown error'}\n"
                f"IMPORTANT: Do NOT guess or invent information from this file. "
                f"Tell the user that the file could not be processed.\n"
                f"=== END FILE CONTEXT ===\n"
            )

        if self.status != FileStatus.READY or not self.chunks:
            return ""

        lines = [
            f"=== UPLOADED FILE CONTEXT ===",
            f"File: {self.filename}",
            f"Type: {self.file_type.value}",
        ]
        if self.page_count:
            lines.append(f"Pages: {self.page_count}")
        lines.append("")
        lines.append("CONTENT:")

        total_chars = sum(len(l) for l in lines)
        for chunk in self.chunks:
            block = chunk.to_prompt_block()
            if total_chars + len(block) > max_chars:
                lines.append("... [content truncated for context window] ...")
                break
            lines.append(block)
            lines.append("")
            total_chars += len(block)

        lines.append("=== END FILE CONTEXT ===")
        lines.append(
            "RULES FOR ANSWERING:\n"
            "1. Answer primarily from the file above. Do not invent facts.\n"
            "2. If a page number is available, cite it (e.g. 'On page 5...').\n"
            "3. If the answer is NOT in the file, say: "
            "'I couldn't find that in the uploaded file.'\n"
            "4. Do not confuse file content with your own identity."
        )
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "filename": self.filename,
            "type": self.file_type.value,
            "status": self.status.value,
            "page_count": self.page_count,
            "chunk_count": len(self.chunks),
            "error": self.error,
        }

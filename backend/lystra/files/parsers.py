
import structlog
import io
import json
import pandas as pd
from typing import Optional

logger = structlog.get_logger(__name__)

class DocumentParser:
    @staticmethod
    def parse(file_bytes: bytes, category: str, filename: str) -> str:
        """Parses verified file bytes into a clean markdown/text string."""
        try:
            if category == "pdf":
                return DocumentParser._parse_pdf(file_bytes)
            elif category == "docx":
                return DocumentParser._parse_docx(file_bytes)
            elif category == "pptx":
                return DocumentParser._parse_pptx(file_bytes)
            elif category in ("xlsx", "csv"):
                return DocumentParser._parse_spreadsheet(file_bytes, category)
            elif category in ("text", "markdown"):
                return file_bytes.decode("utf-8", errors="replace")
            elif category == "json":
                return DocumentParser._parse_json(file_bytes)
            elif category == "xml":
                return DocumentParser._parse_xml(file_bytes)
            elif category == "image":
                # Images are not parsed into text here; they rely on Vision Model during RAG
                return f"[IMAGE DOCUMENT: {filename}] (Content is visually indexed)"
            else:
                raise ValueError(f"Unknown parsing category: {category}")
        except Exception as e:
            logger.error("document_parsing_failed", category=category, error=str(e))
            raise RuntimeError(f"Failed to parse {category} document: {str(e)}")

    @staticmethod
    def _parse_pdf(file_bytes: bytes) -> str:
        import fitz # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text_parts = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            if text.strip():
                text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
        return "\n\n".join(text_parts)

    @staticmethod
    def _parse_docx(file_bytes: bytes) -> str:
        from docx import Document
        doc = Document(io.BytesIO(file_bytes))
        return "\n".join([p.text for p in doc.paragraphs])

    @staticmethod
    def _parse_pptx(file_bytes: bytes) -> str:
        from pptx import Presentation
        prs = Presentation(io.BytesIO(file_bytes))
        text_parts = []
        for i, slide in enumerate(prs.slides):
            slide_text = []
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    slide_text.append(shape.text)
            if slide_text:
                text_parts.append(f"--- Slide {i + 1} ---\n" + "\n".join(slide_text))
        return "\n\n".join(text_parts)

    @staticmethod
    def _parse_spreadsheet(file_bytes: bytes, category: str) -> str:
        if category == "csv":
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))
        # Convert to markdown table format for LLM readability
        return df.to_markdown(index=False)

    @staticmethod
    def _parse_json(file_bytes: bytes) -> str:
        data = json.loads(file_bytes.decode("utf-8"))
        return json.dumps(data, indent=2)

    @staticmethod
    def _parse_xml(file_bytes: bytes) -> str:
        # Basic decode, rely on standard XML for now. 
        # DefusedXML should be used in production for safety against billions laughs attacks.
        return file_bytes.decode("utf-8", errors="replace")


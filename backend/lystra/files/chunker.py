import json

class TextChunker:
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
        """
        Phase 6: Document Structure Preservation.
        Intelligently chunks JSON structural documents by section, falling back to text chunks.
        """
        if not text:
            return []
            
        try:
            # Detect if the parser returned a structural JSON block
            data = json.loads(text)
            chunks = []
            
            if isinstance(data, dict):
                if "sections" in data:
                    for sec in data["sections"]:
                        title = sec.get("title", "")
                        content = sec.get("content", "")
                        page = sec.get("page_start", "")
                        page_ctx = f" (Page {page})" if page else ""
                        text_to_chunk = f"Section: {title}{page_ctx}\n{content}"
                        chunks.extend(TextChunker._basic_chunk(text_to_chunk, chunk_size, overlap))
                    return chunks
                    
                elif "Workbook" in data:
                    for sheet in data["Workbook"]:
                        s_name = sheet.get("Sheet", "")
                        s_headers = str(sheet.get("headers", []))
                        s_content = sheet.get("content", "")
                        text_to_chunk = f"Sheet: {s_name}\nHeaders: {s_headers}\n\n{s_content}"
                        chunks.extend(TextChunker._basic_chunk(text_to_chunk, chunk_size, overlap))
                    return chunks
        except Exception:
            pass # Fall back to basic string chunking
            
        return TextChunker._basic_chunk(text, chunk_size, overlap)

    @staticmethod
    def _basic_chunk(text: str, chunk_size: int, overlap: int) -> list[str]:
        chunks = []
        paragraphs = text.split("\n\n")
        
        current_chunk = ""
        for p in paragraphs:
            if len(p) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                start = 0
                while start < len(p):
                    end = min(start + chunk_size, len(p))
                    chunks.append(p[start:end].strip())
                    start += chunk_size - overlap
                continue
                
            if len(current_chunk) + len(p) + 2 <= chunk_size:
                current_chunk += p + "\n\n"
            else:
                chunks.append(current_chunk.strip())
                current_chunk = p + "\n\n"
                
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
            
        return chunks

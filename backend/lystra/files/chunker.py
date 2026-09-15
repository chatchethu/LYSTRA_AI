
class TextChunker:
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
        """
        Simple recursive/sliding window character chunker.
        Splits by double newline, then single newline, then character limit to respect paragraph boundaries where possible.
        """
        if not text:
            return []
            
        chunks = []
        paragraphs = text.split("\n\n")
        
        current_chunk = ""
        for p in paragraphs:
            # If a single paragraph is too large, hard split it
            if len(p) > chunk_size:
                # Add current if not empty
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""
                
                # Hard slice the massive paragraph
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


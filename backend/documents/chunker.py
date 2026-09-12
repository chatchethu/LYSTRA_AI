from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import uuid
from .parser import ParsedDocument

class Chunk(BaseModel):
    id: str
    document_id: str
    text: str
    chunk_index: int
    page: Optional[int]
    section: Optional[str]
    metadata: Dict[str, Any]

class DocumentChunker:
    """
    Splits ParsedDocuments into manageable chunks for embedding and retrieval.
    """
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, document: ParsedDocument, document_id: str) -> List[Chunk]:
        # A more sophisticated chunker might use sections or LangChain's RecursiveCharacterTextSplitter.
        # This is a basic implementation.
        text_chunks = self._recursive_split(document.text, self.chunk_size)
        
        chunks = []
        for i, text_chunk in enumerate(text_chunks):
            chunks.append(Chunk(
                id=str(uuid.uuid4()),
                document_id=document_id,
                text=text_chunk,
                chunk_index=i,
                page=None, # In a real implementation we would track page boundaries during chunking
                section=None,
                metadata=document.metadata
            ))
        return chunks

    def _recursive_split(self, text: str, max_chars: int) -> List[str]:
        if len(text) <= max_chars:
            return [text]
            
        # Try to split by paragraph first
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            if len(current_chunk) + len(p) + 2 <= max_chars:
                if current_chunk:
                    current_chunk += "\n\n" + p
                else:
                    current_chunk = p
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                # If paragraph itself is larger than max_chars, split it further
                if len(p) > max_chars:
                    chunks.extend(self._split_large_text(p, max_chars))
                    current_chunk = ""
                else:
                    current_chunk = p
                    
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks
        
    def _split_large_text(self, text: str, max_chars: int) -> List[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chars
            # Try to find a space to split on
            if end < len(text):
                last_space = text.rfind(" ", start, end)
                if last_space != -1 and last_space > start:
                    end = last_space
            chunks.append(text[start:end])
            start = end - self.chunk_overlap # Apply overlap
            if start < 0:
                start = 0
        return chunks

    def _split_by_section(self, document: ParsedDocument) -> List[Chunk]:
        # Placeholder for section-based splitting logic
        return []

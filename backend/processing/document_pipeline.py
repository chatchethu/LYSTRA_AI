import uuid
import structlog
import logging
from typing import Optional
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from backend.config import get_settings
from backend.db.models.file import FileChunk
from backend.llm.gateway import LLMGateway
from backend.documents.parser import DocumentParser, ParsedDocument
from backend.documents.chunker import DocumentChunker

logger = structlog.get_logger(__name__)

class DocumentPipeline:
    def __init__(self, db: AsyncSession, llm_gateway: LLMGateway):
        self.db = db
        self.llm_gateway = llm_gateway
        self.parser = DocumentParser()
        self.chunker = DocumentChunker(chunk_size=1000, chunk_overlap=100)

    async def process_file(
        self,
        file_path: str,
        filename: str,
        mime_type: str,
        user_id: uuid.UUID,
        file_id: uuid.UUID,
        conversation_id: Optional[uuid.UUID] = None,
        task_id: Optional[uuid.UUID] = None
    ) -> None:
        """
        Process a file, parse, chunk, embed, and store in the database.
        Handles PDF, text, code, images.
        """
        try:
            parsed_doc = await self._parse_file(file_path, filename, mime_type)
            
            # Chunk the parsed document
            chunks = self.chunker.chunk(parsed_doc, str(file_id))
            
            # Embed and store chunks
            for i, chunk in enumerate(chunks):
                # Ensure text is not empty before embedding
                if not chunk.text.strip():
                    continue
                settings = get_settings()
                embedding = await self.llm_gateway.embed(chunk.text, model=settings.OLLAMA_EMBEDDING_MODEL)
                
                metadata = chunk.metadata.copy()
                metadata.update({
                    "user_id": str(user_id),
                    "file_id": str(file_id),
                    "conversation_id": str(conversation_id) if conversation_id else None,
                    "task_id": str(task_id) if task_id else None,
                })

                stmt = insert(FileChunk).values(
                    id=uuid.uuid4(),
                    file_id=file_id,
                    content=chunk.text,
                    chunk_index=chunk.chunk_index,
                    embedding=embedding,
                    metadata=metadata
                ).on_conflict_do_nothing(
                    index_elements=['file_id', 'chunk_index']
                )
                
                await self.db.execute(stmt)
            
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            await self.db.rollback()
            raise

    async def _parse_file(self, file_path: str, filename: str, mime_type: str) -> ParsedDocument:
        ext = Path(file_path).suffix.lower()
        
        # Text and Code files
        text_extensions = [".py", ".js", ".ts", ".java", ".c", ".cpp", ".rs", ".go", ".txt", ".md", ".json", ".xml", ".yaml", ".yml", ".sh", ".html", ".css", ".csv"]
        if ext in text_extensions or mime_type.startswith("text/"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                return ParsedDocument(
                    filename=filename,
                    content_type=mime_type,
                    text=content,
                    sections=[],
                    tables=[],
                    metadata={"source": filename, "type": "text/code"},
                    page_count=None
                )
            except UnicodeDecodeError:
                pass # Fallback to standard parser if not decodable
            
        # Images
        image_extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]
        if ext in image_extensions or mime_type.startswith("image/"):
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            
            # Generate description using vision model
            prompt = "Describe this image in detail to make it searchable and indexable."
            description = await self.llm_gateway.vision(prompt, image_bytes)
            
            return ParsedDocument(
                filename=filename,
                content_type=mime_type,
                text=f"Image Description for {filename}:\n{description}",
                sections=[],
                tables=[],
                metadata={"source": filename, "type": "image"},
                page_count=1
            )
            
        # Use existing parser for PDF, Word, CSV, etc.
        return await self.parser.parse(file_path, mime_type)

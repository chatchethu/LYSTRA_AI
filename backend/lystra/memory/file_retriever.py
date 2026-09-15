
import uuid
import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models.file import File, FileChunk
from backend.llm.gateway import LLMGateway

logger = structlog.get_logger(__name__)

class FileRetriever:
    def __init__(self, llm_gateway: LLMGateway):
        self.llm = llm_gateway

    async def search_files(self, user_id: str, query: str, limit: int = 5) -> list[dict]:
        """
        Embeds the user query and performs a semantic vector search across all of 
        the users processed file chunks.
        """
        from backend.db.session import AsyncSessionLocal
        try:
            query_embedding = await self.llm.embed(query)
            
            async with AsyncSessionLocal() as db:
                # Semantic search across file chunks belonging to this user
                # We join File to ensure we only search files owned by the user and in "ready" status
                stmt = (
                    select(FileChunk, File.filename)
                    .join(File, FileChunk.file_id == File.id)
                    .where(
                        File.user_id == uuid.UUID(str(user_id)),
                        File.status == "ready"
                    )
                    .order_by(FileChunk.embedding.cosine_distance(query_embedding))
                    .limit(limit)
                )
                
                result = await db.execute(stmt)
                rows = result.all()
                
                retrieved = []
                for chunk, filename in rows:
                    retrieved.append({
                        "filename": filename,
                        "content": chunk.content,
                        "chunk_index": chunk.chunk_index
                    })
                    
                return retrieved
        except Exception as e:
            logger.error("file_retrieval_failed", error=str(e), user_id=user_id)
            return []


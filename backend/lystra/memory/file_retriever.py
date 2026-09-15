
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
                # Phase 19 & 20: Hierarchical and Question-Aware Retrieval
                # Instead of just flat vector distance, we extract a larger candidate pool
                # and sort them by structural relevance and vector distance.
                candidate_limit = limit * 3
                
                stmt = (
                    select(FileChunk, File.filename)
                    .join(File, FileChunk.file_id == File.id)
                    .where(
                        # Phase 43: Strict Semantic Index Security Access Boundary
                        # The JOIN guarantees that pgvector applies the tenant separation BEFORE returning distances.
                        File.user_id == uuid.UUID(str(user_id)),
                        File.status == "ready"
                    )
                    .order_by(FileChunk.embedding.cosine_distance(query_embedding))
                    .limit(candidate_limit)
                )
                
                result = await db.execute(stmt)
                rows = result.all()
                
                candidates = []
                for chunk, filename in rows:
                    # Reranking scoring factors (Phase 19 & 20)
                    score = 0.0
                    content_lower = chunk.content.lower()
                    query_lower = query.lower()
                    
                    # Exact Entity Match Boost
                    if any(word in content_lower for word in query_lower.split() if len(word) > 4):
                        score += 0.2
                        
                    # Structural Boost (Table relevance, Section relevance)
                    if "[TABLE]" in chunk.content or "Section:" in chunk.content or "Sheet:" in chunk.content:
                        score += 0.15
                        
                    # Hierarchical Document Filtering
                    # (In a full implementation, we group chunks by section_id and retrieve section summaries first)
                    
                    candidates.append({
                        "filename": filename,
                        "content": chunk.content,
                        "chunk_index": chunk.chunk_index,
                        "score": score
                    })
                
                # Sort by our computed reranking score (higher is better)
                # Note: cosine_distance is already factored in as they made the top candidate_limit pool
                candidates.sort(key=lambda x: x["score"], reverse=True)
                
                # Return the top N chunks after structural reranking
                return candidates[:limit]
        except Exception as e:
            # Phase 42: Sensitive Data Handling. Do NOT log raw chunks or document exceptions that may contain PI.
            logger.error("file_retrieval_failed", error=str(e), user_id=user_id)
            return []


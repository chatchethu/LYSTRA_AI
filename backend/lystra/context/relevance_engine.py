from typing import List
import math

class MemoryCandidate:
    def __init__(self, content: str, embedding: List[float], recency_score: float, entities: List[str]):
        self.content = content
        self.embedding = embedding
        self.recency_score = recency_score
        self.entities = entities

class RelevanceEngine:
    def __init__(self):
        pass

    def compute_similarity(self, v1: List[float], v2: List[float]) -> float:
        # Simple dot product assuming normalized vectors
        return sum(a * b for a, b in zip(v1, v2))

    def score_context(self, current_embedding: List[float], current_entities: List[str], candidates: List[MemoryCandidate]) -> List[dict]:
        """
        Phase 6: Context Relevance Engine
        semantic similarity + recency + conversation continuity + entity overlap
        """
        scored_candidates = []
        for c in candidates:
            semantic_score = self.compute_similarity(current_embedding, c.embedding)
            
            # Entity overlap bonus
            overlap = set(current_entities).intersection(set(c.entities))
            entity_score = len(overlap) * 0.1
            
            # Combine scores
            final_score = (semantic_score * 0.6) + (c.recency_score * 0.2) + (entity_score * 0.2)
            
            scored_candidates.append({
                "content": c.content,
                "score": final_score
            })
            
        # Sort descending by score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        return scored_candidates

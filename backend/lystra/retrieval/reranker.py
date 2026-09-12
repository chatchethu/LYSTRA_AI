from typing import List

class Reranker:
    def __init__(self, relevance_threshold: float = 0.65):
        self.relevance_threshold = relevance_threshold

    def filter_and_rank(self, candidates: List[dict]) -> List[dict]:
        """
        Phase 13: Retrieval Quality
        Filters out low-relevance memory matches to prevent hallucination 
        and confusing context injection.
        """
        valid_context = []
        for c in candidates:
            if c.get("score", 0.0) >= self.relevance_threshold:
                valid_context.append(c)
                
        # Sort by score descending
        valid_context.sort(key=lambda x: x["score"], reverse=True)
        return valid_context

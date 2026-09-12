from typing import List, Dict, Any
import datetime
import json
import asyncio
import structlog
from .schemas import MemoryObject, MemoryStatus
from backend.config import get_settings

logger = structlog.get_logger(__name__)

class MemoryRanker:
    """
    Phase 12: Ranked Memory Retrieval
    Scores retrieved memories against the current user request.
    """
    def __init__(self, llm_gateway, model: str = "llama3.2:latest"):
        self.llm = llm_gateway
        self.model = model  # Fix: Model name configurable

    def apply_relevance_threshold(self, memories: List[MemoryObject], threshold: float = 0.5) -> List[MemoryObject]:
        # A lightweight heuristic filtering before heavy semantic scoring
        valid = [m for m in memories if m.status in [MemoryStatus.ACTIVE, MemoryStatus.VALIDATED, MemoryStatus.UPDATED]]
        
        # Multiply importance by confidence to get a base weight
        return [m for m in valid if (m.importance * m.confidence) >= threshold]

    async def rank_for_context(self, user_request: str, candidates: List[MemoryObject]) -> List[MemoryObject]:
        """
        Phase 13: Semantic Memory Ranking
        Scores retrieved memories against the current user request using semantic relevance.
        """
        filtered = self.apply_relevance_threshold(candidates, threshold=0.3)
        if not filtered:
            return []
            
        # If there are many, trim before LLM call to save tokens
        filtered.sort(key=lambda m: m.importance * m.confidence, reverse=True)
        filtered = filtered[:10]
        
        # Mapping index to memory instead of full UUID (cheaper, more robust)
        idx_to_mem = {str(i): m for i, m in enumerate(filtered)}
        
        mem_json = []
        for idx_str, m in idx_to_mem.items():
            mem_json.append({
                "id": idx_str,
                "type": m.type.value if hasattr(m.type, "value") else m.type,
                "content": str(m.value)[:500],
                "importance": m.importance,
                "confidence": m.confidence,
                "source": m.source.value if hasattr(m.source, "value") else m.source
            })
            
        prompt = f"""Evaluate these memories against the user's current request.
User Request: {user_request}
Memories: {json.dumps(mem_json)}

For each memory, output a JSON object with:
"memory_id": the id (the integer string provided)
"relevance": float between 0.0 and 1.0 (how useful it is for this exact request)
"confidence": float between 0.0 and 1.0 (how certain you are of this relevance)
"reason": short reason

Return ONLY a JSON array of these objects."""

        messages = [
            {"role": "system", "content": "You are a semantic memory ranker."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            settings = get_settings()
            # Fix: Add timeout to prevent hanging the retrieval path
            resp_str = await asyncio.wait_for(
                self.llm.chat(messages, model=self.model, format="json"), 
                timeout=settings.MEMORY_CLASSIFICATION_TIMEOUT_S
            )
            
            # Clean possible markdown wrapping
            clean_text = resp_str.replace("```json", "").replace("```", "").strip()
            
            # Use raw_decode to robustly extract the FIRST valid JSON value from the
            # response. This handles all malformed LLM outputs:
            #   - Trailing garbage after valid JSON (causes "Extra data" with json.loads)
            #   - Two JSON values back-to-back (e.g. [] [])
            #   - Text before/after the JSON array
            # Strategy: find the first '[' or '{', then raw_decode from there.
            decoder = json.JSONDecoder()
            rankings = None
            for start_char in ("[", "{"):
                idx = clean_text.find(start_char)
                if idx != -1:
                    try:
                        val, _ = decoder.raw_decode(clean_text, idx)
                        rankings = val
                        break
                    except json.JSONDecodeError:
                        continue
            
            if rankings is None:
                raise ValueError("No valid JSON found in LLM ranking response")
            
            # Handle when LLM wraps list in a dict (e.g. {"rankings": [...]})
            if isinstance(rankings, dict):
                found_list = False
                for v in rankings.values():
                    if isinstance(v, list):
                        rankings = v
                        found_list = True
                        break
                # If it's just a single object returned instead of a list, wrap it in a list
                if not found_list and "memory_id" in rankings:
                    rankings = [rankings]
            
            if not isinstance(rankings, list):
                raise ValueError(f"Expected list, got {type(rankings)}")
            
            scored = []
            for rank in rankings:
                if not isinstance(rank, dict):
                    continue
                    
                mem_id = str(rank.get("memory_id", ""))
                relevance = rank.get("relevance", 0)
                confidence = rank.get("confidence", 0)
                
                if mem_id in idx_to_mem and isinstance(relevance, (int, float)) and isinstance(confidence, (int, float)):
                    # Compute effective score
                    effective_score = relevance * confidence
                    if effective_score > 0.4:  # Using effective score threshold
                        scored.append((effective_score, idx_to_mem[mem_id]))
            
            if not scored:
                # Explicit fallback instead of returning [] silently
                return filtered[:3]
                
            # Fix #4: Sort explicitly by effective_score before taking top 5
            scored.sort(key=lambda x: x[0], reverse=True)
            return [m for _, m in scored[:5]]
            
        except asyncio.TimeoutError:
            logger.warning("memory_ranking_timeout")
            return filtered[:3]
        except Exception as e:
            logger.warning("memory_ranking_failed", error=str(e))
            return filtered[:3]

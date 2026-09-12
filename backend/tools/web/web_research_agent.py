"""
Web Research Agent — LYSTRA Intelligence V2
Phase 10 & 11: Multi-Step web research agent. 
Breaks complex queries into multiple searches, cross-checks, and extracts facts.
"""
from typing import Dict, Any, List
import json
import asyncio
import uuid
import structlog
from backend.tools.web.web_search import WebSearchTool

logger = structlog.get_logger("lystra.research_agent")

class WebResearchAgent:
    """
    Orchestrates multiple searches and builds a verified fact base before
    returning to the main conversational agent.
    """
    
    def __init__(self, llm_gateway, model_router=None):
        self.llm = llm_gateway
        self.model_router = model_router
        self.search_tool = WebSearchTool()
        
    async def _generate_subqueries(self, query: str) -> List[str]:
        prompt = f"""You are an expert research assistant. 
The user needs deep, comprehensive research on this topic: "{query}"

Break this complex topic down into 3 highly specific, orthogonal search queries that will yield the best technical, factual, and comprehensive coverage of the topic.
Do not use generic queries.

Return ONLY a JSON array of strings:
["query 1", "query 2", "query 3"]
"""
        try:
            from backend.config import get_settings
            
            # Fix #1: Route through the same model_router used elsewhere
            if self.model_router and hasattr(self.model_router, "select_model"):
                model = await self.model_router.select_model(task="subquery_generation")
            elif self.model_router and hasattr(self.model_router, "get_model"):
                from backend.llm.model_router import TaskType
                model = self.model_router.get_model(TaskType.REASONING)
            else:
                model = get_settings().OLLAMA_CHAT_MODEL
                
            messages = [{"role": "user", "content": prompt}]
            response = await self.llm.chat(messages=messages, model=model, format="json")
            # Parse it out
            data = json.loads(response)
            
            # If the model returned an object with a key instead of a raw array:
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, list) and v:
                        return [str(i) for i in v][:3]
            
            # Fix #4: Empty subquery list silently failed
            if isinstance(data, list) and data:
                return [str(i) for i in data][:3]
                
            return [query, f"{query} details"]
        except Exception as e:
            logger.warning("research_subquery_generation_failed", error=str(e))
            return [query, f"{query} technical details", f"{query} analysis"]

    async def _safe_stream(self, stream_callback, content: str):
        # Fix #6: stream_callback failures aren't isolated
        if stream_callback:
            try:
                await stream_callback(content)
            except Exception as e:
                logger.warning("research_stream_callback_failed", error=str(e))

    async def deep_research(
        self,
        query: str,
        user_id: Any = "research-agent",
        stream_callback = None
    ) -> Dict[str, Any]:
        """
        Executes a multi-step research loop.
        """
        logger.info("deep_research_started", query=query)
        
        await self._safe_stream(stream_callback, "*(Planning research strategy...)*\n\n")
            
        subqueries = await self._generate_subqueries(query)
        logger.info("deep_research_subqueries", subqueries=subqueries)
        
        all_sources = []
        fact_base = []
        
        async def run_step(i, sq):
            await self._safe_stream(stream_callback, f"*(Researching step {i+1}/{len(subqueries)}: {sq}...)*\n\n")
            
            logger.info("deep_research_step", step=i+1, subquery=sq)
            
            # Fix #5: No timeouts on search calls
            res = await asyncio.wait_for(
                self.search_tool.execute(
                    user_id=user_id, 
                    queries=[sq], 
                    max_results=3,
                    llm=self.llm,
                    model_router=self.model_router
                ),
                timeout=500.0
            )
            return i, sq, res
            
        # Fix #2: asyncio.gather with return_exceptions=True
        results = await asyncio.gather(
            *(run_step(i, sq) for i, sq in enumerate(subqueries)),
            return_exceptions=True
        )
        
        # Process successful results
        successes = [r for r in results if not isinstance(r, Exception)]
        for r in results:
            if isinstance(r, Exception):
                logger.error("deep_research_step_exception", error=str(r))
        
        for i, sq, res in sorted(successes, key=lambda x: x[0]):
            data = res.data if hasattr(res, "data") else res
            if getattr(res, "success", True) and isinstance(data, dict) and "sources" in data:
                for src in data["sources"]:
                    # Fix #3: Unsafe dict indexing
                    src["source_id"] = f"s{i+1}_{src.get('source_id', uuid.uuid4().hex[:8])}"
                all_sources.extend(data["sources"])
                fact_base.append(f"--- Evidence for: {sq} ---\n{data.get('formatted', '')}")
            else:
                logger.warning("deep_research_subquery_failed", subquery=sq, step=i+1)
                
        logger.info("deep_research_complete", total_sources=len(all_sources))
        
        await self._safe_stream(stream_callback, "*(Compiling final report...)*\n\n")
        
        # Deduplicate sources by URL
        unique_sources = {s["url"]: s for s in all_sources if "url" in s}.values()
        compiled_evidence = "\n\n".join(fact_base)
        
        return {
            "evidence": compiled_evidence,
            "sources": list(unique_sources),
            "status": "complete"
        }

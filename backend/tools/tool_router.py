import json
import asyncio
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, model_validator
import structlog

from backend.config import get_settings
from backend.lystra.routing.terms import (
    USER_IDENTITY_TERMS,
    IDENTITY_TERMS,
    DEEP_RESEARCH_TERMS,
    STATIC_EXPLANATION_PREFIXES,
    MANDATORY_WEB_TERMS,
    ENTERTAINMENT_WEB_TERMS,
    CASUAL_TERMS,
    PERSONAL_TERMS,
    contains_term as _contains_term,
    build_search_query as _build_search_query,
)

logger = structlog.get_logger(__name__)

class RoutePriority(str, Enum):
    IDENTITY = "IDENTITY"
    CONVERSATION = "CONVERSATION"
    PERSONAL = "PERSONAL"
    TASK = "TASK"
    TOOL = "TOOL"

class WebSearchPolicy(str, Enum):
    MANDATORY_WEB = "MANDATORY_WEB"
    DEEP_RESEARCH = "DEEP_RESEARCH"
    OPTIONAL_WEB = "OPTIONAL_WEB"
    NO_WEB = "NO_WEB"

class ToolRoutingDecision(BaseModel):
    web_policy: WebSearchPolicy
    reasoning: str
    route_priority: RoutePriority = RoutePriority.TASK
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    search_query: Optional[str] = None
    
    @model_validator(mode="after")
    def enforce_consistency(self):
        # IDENTITY, CONVERSATION, and PERSONAL always NO_WEB
        if self.route_priority in (RoutePriority.IDENTITY, RoutePriority.CONVERSATION, RoutePriority.PERSONAL):
            if self.web_policy != WebSearchPolicy.NO_WEB:
                logger.info(
                    "tool_router_policy_override",
                    original_policy=self.web_policy.value,
                    route_priority=self.route_priority.value,
                )
            self.web_policy = WebSearchPolicy.NO_WEB
            self.search_query = None
        return self

# Fix #3: Added explicit rule for User's own identity mapped to PERSONAL.
_ROUTER_PROMPT = """You are the Tool Routing Engine for LYSTRA.
Your job is to decide whether a web search is required to answer the user's message.

ROUTING PRIORITY
1. Internal LYSTRA identity ("who are you") → NO_WEB, route=IDENTITY
2. Ordinary casual conversation, greetings → NO_WEB, route=CONVERSATION  
3. User's own identity/memory ("who am I", "my preferences") → NO_WEB, route=PERSONAL
4. Personal/emotional sharing → NO_WEB, route=PERSONAL
5. Explaining stable/universal concepts (recursion, sorting, gravity) → NO_WEB, route=TASK
6. Movie, music, book, food, place, travel, or entertainment recommendations → MANDATORY_WEB, route=TOOL
   (Regional content especially — Kannada, Tamil, Telugu, Malayalam, Hindi movies/shows/songs)
   (LLM knowledge of regional entertainment is unreliable — always search for accurate results)
7. News, current events, prices, stocks, weather, sports results → MANDATORY_WEB, route=TOOL
8. Any other external/factual information that benefits from accuracy → OPTIONAL_WEB, route=TOOL
9. Deep research requested explicitly → DEEP_RESEARCH, route=TOOL

Do not use WEB merely because the user asked a 'what', 'who', 'where' question.
Use WEB only when the answer requires current or external information, or regional-specific content.
NEVER search the web for questions about the user's personal identity (e.g. 'who am i', 'what is my name', 'do you know me'). This is answered natively from internal DB memory.

Recent Conversation Context:
<untrusted_history>
{history}
</untrusted_history>

User message: <untrusted_message>{message}</untrusted_message>

Semantic Analysis of the User Message:
<semantic_data>
{understanding}
</semantic_data>

Output ONLY a JSON object (no explanation, no markdown):
{{
    "web_policy": "MANDATORY_WEB | OPTIONAL_WEB | NO_WEB | DEEP_RESEARCH",
    "search_query": "the actual search query string, or null if web_policy is NO_WEB",
    "reasoning": "one sentence justification",
    "route_priority": "TOOL | TASK | CONVERSATION | IDENTITY | PERSONAL",
    "confidence": 0.9
}}

IMPORTANT rules for search_query:
- If web_policy is NO_WEB → set search_query to null (not a string, the JSON null value)
- If web_policy requires web search → write a real, specific search query based on the user message
- NEVER copy this instruction text into search_query
- BAD example: "optimized google search string if needed"
- GOOD example: "best Kannada movies 2023 2024 to watch"
"""

_HISTORY_WINDOW = 3

# Fix #5: Validator for search query.
def _validate_search_query(q: str, max_len: int = 200) -> str:
    q = _build_search_query(q)
    q = q.strip()[:max_len]
    if not q:
        raise ValueError("empty search query")
    # Reject placeholder text that the LLM sometimes copies verbatim from the prompt example
    _PLACEHOLDER_MARKERS = [
        "optimized google search string",
        "actual search query string",
        "the actual search query",
        "if needed, else null",
        "search query string",
    ]
    q_lower = q.lower()
    for marker in _PLACEHOLDER_MARKERS:
        if marker in q_lower:
            raise ValueError(f"search_query looks like a template placeholder: {q!r}")
    return q

class ToolRouter:
    def __init__(self, llm_gateway):
        self.llm = llm_gateway

    def _deterministic_route(self, message: str, understanding: Any = None) -> Optional[ToolRoutingDecision]:
        if not message:
            return ToolRoutingDecision(web_policy=WebSearchPolicy.NO_WEB, reasoning="Empty message.", route_priority=RoutePriority.CONVERSATION, confidence=1.0)
            
        text = message.lower().strip()
        
        # 1. Identity check first
        if _contains_term(text, USER_IDENTITY_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="User identity question — answered internally.",
                route_priority=RoutePriority.PERSONAL,
                confidence=1.0
            )
            logger.info("tool_router_decision", intent="user_identity", route="PERSONAL", web_policy="NO_WEB", confidence=1.0)
            return result
            
        if _contains_term(text, IDENTITY_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Identity question — answered internally.",
                route_priority=RoutePriority.IDENTITY,
                confidence=1.0
            )
            logger.info("tool_router_decision", intent="system_identity", route="IDENTITY", web_policy="NO_WEB", confidence=1.0)
            return result

        # 2. Deep Research explicitly requested
        if _contains_term(text, DEEP_RESEARCH_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.DEEP_RESEARCH,
                reasoning="Explicit request for deep research.",
                route_priority=RoutePriority.TOOL,
                confidence=0.95,
                search_query=_build_search_query(message)
            )
            logger.info("tool_router_decision", intent="deep_research", route="TOOL", web_policy="DEEP_RESEARCH", confidence=0.95)
            return result

        # Fix #1: Date/time is always local — check BEFORE generic mandatory web terms like "today".
        if any(text.startswith(p) for p in ("what time", "what day", "what is the date", "what is today")):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Date/time query answered from system clock, not web.",
                route_priority=RoutePriority.TASK,
                confidence=1.0,
            )
            logger.info("tool_router_decision", intent="date_time_local", route="TASK", web_policy="NO_WEB", confidence=1.0)
            return result

        # 3. (Removed: MANDATORY_WEB and ENTERTAINMENT_WEB deterministic paths)
        # We now rely on the LLM router for these so it can generate a clean, optimized
        # search query instead of passing the user's conversational typo-filled message directly to the search engine.

        # 4. Stable conceptual explanations check
        if any(text.startswith(prefix) for prefix in STATIC_EXPLANATION_PREFIXES):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Stable conceptual explanation does not require web search.",
                route_priority=RoutePriority.TASK,
                confidence=0.95,
            )
            logger.info("tool_router_decision", intent="stable_explanation", route="TASK", web_policy="NO_WEB", confidence=0.95)
            return result

        # 5. Understanding context check (Semantic NLU dynamic check)
        # Fix #10: explicitly checking is not None.
        if understanding is not None:
            if getattr(understanding, "is_fallback", False):
                logger.info("tool_router_ignoring_understanding", reason="semantic_analysis_fallback")
            else:
                raw_intent = getattr(understanding, "intent", "") or ""
                intent = getattr(raw_intent, "primary", str(raw_intent))
                speech_act = getattr(understanding, "speech_act", "") or ""
                
                CASUAL_INTENTS = {"greeting", "casual_conversation", "small_talk", "farewell", "social", "conversation"}
                PERSONAL_INTENTS = {"emotional_support", "venting", "complaint", "personal_sharing"}
                
                if intent in CASUAL_INTENTS or speech_act in ("greeting", "farewell", "small_talk"):
                    result = ToolRoutingDecision(
                        web_policy=WebSearchPolicy.NO_WEB,
                        reasoning=f"Casual conversation intent={intent}.",
                        route_priority=RoutePriority.CONVERSATION,
                        confidence=1.0
                    )
                    logger.info("tool_router_decision", intent=intent, route="CONVERSATION", web_policy="NO_WEB", confidence=1.0)
                    return result
                    
                if intent in PERSONAL_INTENTS:
                    result = ToolRoutingDecision(
                        web_policy=WebSearchPolicy.NO_WEB,
                        reasoning=f"Personal/emotional conversation intent={intent}.",
                        route_priority=RoutePriority.PERSONAL,
                        confidence=1.0
                    )
                    logger.info("tool_router_decision", intent=intent, route="PERSONAL", web_policy="NO_WEB", confidence=1.0)
                    return result
                
        # 6. Heuristic casual check (Fallbacks if intent parsing failed but keywords match)
        if _contains_term(text, CASUAL_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Casual greeting matched.",
                route_priority=RoutePriority.CONVERSATION,
                confidence=0.9
            )
            logger.info("tool_router_decision", intent="casual_match", route="CONVERSATION", web_policy="NO_WEB", confidence=0.9)
            return result

        # Fix #9: Document dead code explicitly.
        # TODO: currently unreachable — PERSONAL_TERMS is empty pending semantic analyzer rollout.
        if _contains_term(text, PERSONAL_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Personal/emotional content matched.",
                route_priority=RoutePriority.PERSONAL,
                confidence=0.9
            )
            logger.info("tool_router_decision", intent="personal_match", route="PERSONAL", web_policy="NO_WEB", confidence=0.9)
            return result

        return None

    def _sanitize_for_prompt(self, text: str) -> str:
        """Escape < and > to prevent early tag closure prompt injection."""
        if not text:
            return ""
        return text.replace("<", "&lt;").replace(">", "&gt;")

    # Fix #6: `history: list = None` changed to `history: Optional[list] = None`
    async def route(self, message: str, history: Optional[list] = None, understanding: Any = None) -> ToolRoutingDecision:
        # 1. Deterministic Fast-Path
        decision = self._deterministic_route(message, understanding)
        if decision:
            return decision

        # 2. LLM Evaluation Path
        settings = get_settings()
        # Fix #4: Narrowed exception to avoid swallowing misconfiguration silently.
        try:
            model = settings.TOOL_ROUTING_MODEL
            timeout = settings.TOOL_ROUTING_TIMEOUT_S
        except AttributeError:
            logger.warning("tool_router_settings_missing", fallback_model="llama3.2:latest")
            model = "llama3.2:latest"
            timeout = 500.0

        history = history or []
        history_text = "\n".join([str(h) for h in history[-_HISTORY_WINDOW:]])
        
        # Security: Escape tags
        # Fix #7: Cap message to ~2000 chars before prompt insertion to avoid context bloat.
        capped_message = message[:2000]
        if len(message) > 2000:
            logger.debug("tool_router_message_truncated", original_len=len(message), truncated_len=2000)
        
        safe_history = self._sanitize_for_prompt(history_text)
        safe_message = self._sanitize_for_prompt(capped_message)

        if understanding is not None:
            try:
                understanding_json = understanding.model_dump_json() if hasattr(understanding, "model_dump_json") else str(understanding)
            except Exception:
                understanding_json = "{}"
        else:
            understanding_json = "{}"

        # Fix #2: Sanitize understanding_json as well! If any string field has injection it could break out.
        understanding_json = self._sanitize_for_prompt(understanding_json)

        prompt = _ROUTER_PROMPT.format(
            history=safe_history,
            message=safe_message,
            understanding=understanding_json
        )

        # Fix #8: Added a single retry attempt.
        max_attempts = 2
        for attempt in range(1, max_attempts + 1):
            try:
                res = await asyncio.wait_for(
                    self.llm.chat(
                        messages=[{"role": "user", "content": prompt}],
                        model=model,
                        format="json",
                        temperature=0.0
                    ),
                    timeout=timeout
                )
                break  # Successful response, exit retry loop
            except asyncio.TimeoutError:
                logger.warning("tool_router_llm_timeout", attempt=attempt, max_attempts=max_attempts)
                if attempt == max_attempts:
                    # Fix #11: Metrics counter logs (easy to grok for downstream aggregators)
                    logger.info("tool_router_fallback_triggered", reason="timeout", web_policy="OPTIONAL_WEB")
                    return ToolRoutingDecision(
                        web_policy=WebSearchPolicy.OPTIONAL_WEB,
                        reasoning="Routing engine timed out. Defaulting to optional.",
                        route_priority=RoutePriority.TASK,
                        confidence=0.3
                    )
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning("tool_router_llm_network_error", error=str(e), attempt=attempt, max_attempts=max_attempts)
                if attempt == max_attempts:
                    logger.info("tool_router_fallback_triggered", reason="network_error", web_policy="OPTIONAL_WEB")
                    return ToolRoutingDecision(
                        web_policy=WebSearchPolicy.OPTIONAL_WEB,
                        reasoning="Routing engine network error. Defaulting to optional.",
                        route_priority=RoutePriority.TASK,
                        confidence=0.3
                    )
                await asyncio.sleep(0.5)

        try:
            data = json.loads(res)
        except json.JSONDecodeError:
            logger.warning("tool_router_invalid_json", raw_response=res[:500])
            logger.info("tool_router_fallback_triggered", reason="invalid_json", web_policy="OPTIONAL_WEB")
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.OPTIONAL_WEB,
                reasoning="LLM returned non-JSON output. Defaulting to optional.",
                route_priority=RoutePriority.TASK,
                confidence=0.3
            )

        try:
            decision = ToolRoutingDecision(**data)
            
            # Security / Fix #5: Apply true validation to the search query.
            if decision.search_query:
                try:
                    decision.search_query = _validate_search_query(decision.search_query)
                except ValueError as ve:
                    logger.warning("tool_router_search_query_rejected", reason=str(ve))
                    decision.search_query = None  # falls back to raw user_message at call site
                
            # Fix #11: Clear structured logs that can be used for metrics tracking
            logger.info(
                "tool_router_decision",
                intent="llm_evaluated",
                route=decision.route_priority.value,
                web_policy=decision.web_policy.value,
                confidence=decision.confidence
            )
            return decision
        except Exception as e:
            logger.warning("tool_router_schema_error", error=str(e), raw_response=str(data)[:500])
            logger.info("tool_router_fallback_triggered", reason="schema_error", web_policy="OPTIONAL_WEB")
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.OPTIONAL_WEB,
                reasoning="Routing engine schema error. Defaulting to optional.",
                route_priority=RoutePriority.TASK,
                confidence=0.3
            )

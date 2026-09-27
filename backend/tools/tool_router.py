"""
Tool Routing Engine for LYSTRA.

Architecture:
  - Only two deterministic checks remain:
      1. Empty message → no-op (architecturally safe)
      2. Lystra self-identity phrases → NO_WEB (safe: these are static and never need web)
  - Everything else is evaluated by the LLM using full semantic context.
  - The LLM receives: current timestamp, recent history, the user message, and a rich
    SemanticUnderstanding object already produced by the semantic analyzer.
  - The LLM generates 1–3 optimised search queries when web search is needed.

Design rules:
  - NO hardcoded keyword arrays for routing decisions.
  - NO deterministic heuristics for "casual", "entertainment", "explanations", etc.
  - The AI thinks. We validate and sanitise its output.
"""

import json
import asyncio
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, List
from pydantic import BaseModel, Field, model_validator
import structlog

from backend.config import get_settings
from backend.lystra.routing.terms import (
    build_search_query as _build_search_query,
    contains_term as _contains_term,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Enums & Data Models
# ---------------------------------------------------------------------------

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
    search_queries: Optional[List[str]] = None

    @model_validator(mode="after")
    def enforce_consistency(self) -> "ToolRoutingDecision":
        """
        Architectural invariant: IDENTITY, CONVERSATION, PERSONAL never trigger web search.
        If the LLM somehow sets web_policy=MANDATORY_WEB on a greeting, this corrects it.
        """
        if self.route_priority in (
            RoutePriority.IDENTITY,
            RoutePriority.CONVERSATION,
            RoutePriority.PERSONAL,
        ):
            if self.web_policy != WebSearchPolicy.NO_WEB:
                logger.info(
                    "tool_router_policy_override",
                    original_policy=self.web_policy.value,
                    route_priority=self.route_priority.value,
                )
            self.web_policy = WebSearchPolicy.NO_WEB
            self.search_queries = None
        return self


# ---------------------------------------------------------------------------
# LLM Prompt
# ---------------------------------------------------------------------------

_ROUTER_PROMPT = """\
You are the intelligent Tool Routing Engine for LYSTRA AI.
Current Date and Time: {current_time} ({day_of_week})

Your task is to analyse the user's message and decide:
  1. Whether a web search is needed.
  2. If yes, what highly-targeted search queries to run.

== ROUTING FRAMEWORK ==

Use the following framework to reason — do not pattern-match keywords:

NO_WEB situations (answer from memory / reasoning alone):
  - The user is just chatting, greeting, or sharing personal feelings.
  - The user asks about Lystra's own identity, capabilities, or origin.
  - The user asks about their own stored identity ("who am i", "my name", "my preferences").
  - The question is about a timeless concept or skill (maths, algorithms, grammar, logic).
  - The user asks what date/time it is — you know it from the timestamp above.

MANDATORY_WEB situations (must fetch fresh external data):
  - Movie, music, book, game, or entertainment recommendations (especially regional: Kannada,
    Tamil, Telugu, Malayalam, Hindi, Bollywood). LLM knowledge of these is unreliable.
  - News, current events, recent sports results, election outcomes, breaking stories.
  - Live prices: stocks, crypto, commodities, product prices.
  - Weather, forecasts, air quality, travel advisories.
  - Tutorials, learning resources, courses, documentation — if the user asks where to start
    learning something, search for the best current resources, roadmaps, and sites.
  - Software versions, release notes, changelogs, API references.
  - Restaurants, places to visit, hotels, local services.
  - Any topic where your training data may be outdated or wrong.

OPTIONAL_WEB situations (search to improve accuracy, not strictly required):
  - General factual questions where you have some knowledge but freshness adds value.
  - Research-adjacent queries where a cited source improves trustworthiness.

DEEP_RESEARCH situations:
  - The user explicitly asks for a comprehensive report, in-depth analysis, or deep research.

== SEARCH QUERY GENERATION ==

When web search is needed, generate 1–3 highly targeted search queries:
  - Write like a skilled researcher typing into Google, not like a conversational question.
  - Be specific and concise. Prefer keyword-rich queries over full sentences.
  - Include the current year ({current_year}) only when recency genuinely matters.
  - Decompose multi-part questions into separate targeted queries.
  - For learning resources, include words like "roadmap", "best resources", "beginner guide",
    "free tutorials", "top courses" as appropriate.
  - For regional entertainment, include the language name and year range.
  - NEVER copy this prompt text into a query.
  - NEVER use placeholder text like "query 1" or "search string here".

== CONTEXT ==

Recent conversation:
<history>
{history}
</history>

Current user message:
<message>{message}</message>

Semantic analysis already performed on this message:
<semantic_understanding>
{understanding}
</semantic_understanding>

== OUTPUT ==

Respond with ONLY a JSON object — no explanation, no markdown, no prose:
{{
    "web_policy": "MANDATORY_WEB | OPTIONAL_WEB | NO_WEB | DEEP_RESEARCH",
    "route_priority": "TOOL | TASK | CONVERSATION | IDENTITY | PERSONAL",
    "search_queries": ["query 1", "query 2"] or null,
    "reasoning": "one concise sentence explaining this decision",
    "confidence": 0.0
}}

Rules:
  - "search_queries" must be null if "web_policy" is "NO_WEB".
  - "search_queries" must be a non-empty list if web search is needed.
  - "confidence" is a float between 0.0 and 1.0 reflecting how certain you are.
"""

_HISTORY_WINDOW = 5  # slightly wider window for better contextual decisions


# ---------------------------------------------------------------------------
# Query Validation
# ---------------------------------------------------------------------------

# These markers detect when the LLM accidentally copied prompt template text
# into a query. Detected queries are dropped; if all are dropped, we fall back.
_QUERY_TEMPLATE_MARKERS = frozenset([
    "query 1", "query 2", "query 3",
    "search string here", "optimized google search",
    "actual search query", "the actual search query",
    "if needed else null", "search query string",
    "insert query here",
])


def _validate_search_queries(queries: List[str], max_len: int = 250) -> List[str]:
    """
    Validate and sanitise a list of LLM-generated search queries.
    Drops empty strings, over-long strings, and obvious template placeholders.
    Raises ValueError if nothing survives, so the caller can fall back gracefully.
    """
    valid: List[str] = []
    for raw in queries:
        if not isinstance(raw, str):
            continue
        q = raw.strip()
        if not q or len(q) > max_len:
            continue
        q_lower = q.lower()
        if any(marker in q_lower for marker in _QUERY_TEMPLATE_MARKERS):
            logger.debug("tool_router_query_placeholder_dropped", query=q)
            continue
        valid.append(q)

    if not valid:
        raise ValueError("All generated search queries were empty or invalid placeholders.")
    return valid


# ---------------------------------------------------------------------------
# Lystra self-identity check — the only static keyword guard remaining.
# This is architecturally safe: these phrases unambiguously refer to Lystra itself
# and will NEVER need a web search regardless of context.
# ---------------------------------------------------------------------------

_LYSTRA_SELF_IDENTITY_PHRASES = [
    "who are you", "what are you", "tell me about yourself",
    "are you an ai", "are you ai", "are you human", "are you a robot",
    "are you alive", "what can you do", "who made you", "who created you",
    "who built you", "your name", "introduce yourself", "what is lystra",
    "what is your name", "are you lystra",
]

_USER_SELF_IDENTITY_PHRASES = [
    "who am i", "what is my name", "do you know me", "what do you know about me",
    "my details", "remember me", "my preferences", "about me", "know me",
    "know about me", "about myself",
]


# ---------------------------------------------------------------------------
# ToolRouter
# ---------------------------------------------------------------------------

class ToolRouter:
    """
    Routes each turn to the appropriate handling strategy.

    Fast-path (deterministic):
      - Empty message → CONVERSATION / NO_WEB
      - Lystra self-identity → IDENTITY / NO_WEB   (architecturally certain)
      - User self-identity → PERSONAL / NO_WEB     (architecturally certain)
      - Semantic understanding already signals casual/personal → NO_WEB

    Slow-path (LLM):
      - Everything else is evaluated by the LLM with full context.
    """

    def __init__(self, llm_gateway: Any):
        self.llm = llm_gateway

    # ------------------------------------------------------------------
    # Deterministic fast-path
    # ------------------------------------------------------------------

    def _deterministic_route(
        self,
        message: str,
        understanding: Any = None,
    ) -> Optional[ToolRoutingDecision]:
        """
        Returns a ToolRoutingDecision only when the correct answer is
        architecturally certain regardless of content. Returns None otherwise,
        deferring to the LLM.
        """
        if not message or not message.strip():
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Empty message — nothing to route.",
                route_priority=RoutePriority.CONVERSATION,
                confidence=1.0,
            )

        text = message.lower().strip()

        # Lystra self-identity — always NO_WEB, always IDENTITY
        if _contains_term(text, _LYSTRA_SELF_IDENTITY_PHRASES):
            logger.info("tool_router_decision", intent="lystra_identity", web_policy="NO_WEB", confidence=1.0)
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Message refers to Lystra's own identity — answered internally.",
                route_priority=RoutePriority.IDENTITY,
                confidence=1.0,
            )

        # User self-identity — always NO_WEB, answered from DB memory
        if _contains_term(text, _USER_SELF_IDENTITY_PHRASES):
            logger.info("tool_router_decision", intent="user_identity", web_policy="NO_WEB", confidence=1.0)
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Message refers to the user's own stored identity — answered from memory.",
                route_priority=RoutePriority.PERSONAL,
                confidence=1.0,
            )

        # SemanticUnderstanding already classified this as casual or personal — trust it
        if understanding is not None and not getattr(understanding, "is_fallback", False):
            raw_intent = getattr(understanding, "intent", "") or ""
            intent = str(getattr(raw_intent, "primary", raw_intent)).lower()
            speech_act = str(getattr(understanding, "speech_act", "") or "").lower()

            _casual = {"greeting", "casual_conversation", "small_talk", "farewell", "social", "conversation", "chitchat"}
            _personal = {"emotional_support", "venting", "complaint", "personal_sharing", "mental_health"}

            if intent in _casual or speech_act in {"greeting", "farewell", "small_talk", "chitchat"}:
                logger.info("tool_router_decision", intent=intent, web_policy="NO_WEB", confidence=1.0)
                return ToolRoutingDecision(
                    web_policy=WebSearchPolicy.NO_WEB,
                    reasoning=f"Semantic analysis classified intent as casual ({intent}) — no web search needed.",
                    route_priority=RoutePriority.CONVERSATION,
                    confidence=1.0,
                )

            if intent in _personal:
                logger.info("tool_router_decision", intent=intent, web_policy="NO_WEB", confidence=1.0)
                return ToolRoutingDecision(
                    web_policy=WebSearchPolicy.NO_WEB,
                    reasoning=f"Semantic analysis classified intent as personal/emotional ({intent}) — no web search needed.",
                    route_priority=RoutePriority.PERSONAL,
                    confidence=1.0,
                )

        return None  # Defer to LLM

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sanitize_for_prompt(self, text: str) -> str:
        """Escape < and > to prevent prompt injection via untrusted content."""
        if not text:
            return ""
        return text.replace("<", "&lt;").replace(">", "&gt;")

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def route(
        self,
        message: str,
        history: Optional[list] = None,
        understanding: Any = None,
    ) -> ToolRoutingDecision:
        # 1. Fast-path: architecturally certain decisions
        decision = self._deterministic_route(message, understanding)
        if decision:
            return decision

        # 2. Slow-path: LLM evaluation
        settings = get_settings()
        try:
            model = settings.TOOL_ROUTING_MODEL
            timeout = settings.TOOL_ROUTING_TIMEOUT_S
        except AttributeError:
            logger.warning("tool_router_settings_missing", fallback_model="llama3.2:latest")
            model = "llama3.2:latest"
            timeout = 500.0

        history = history or []
        history_text = "\n".join(str(h) for h in history[-_HISTORY_WINDOW:])

        # Cap message length to avoid context bloat
        capped_message = message[:2000]
        if len(message) > 2000:
            logger.debug("tool_router_message_truncated", original_len=len(message))

        # Sanitize untrusted inputs before prompt injection
        safe_history = self._sanitize_for_prompt(history_text)
        safe_message = self._sanitize_for_prompt(capped_message)

        if understanding is not None:
            try:
                understanding_json = (
                    understanding.model_dump_json()
                    if hasattr(understanding, "model_dump_json")
                    else str(understanding)
                )
            except Exception:
                understanding_json = "{}"
        else:
            understanding_json = "{}"
        understanding_json = self._sanitize_for_prompt(understanding_json)

        now = datetime.now(timezone.utc)
        prompt = _ROUTER_PROMPT.format(
            current_time=now.strftime("%Y-%m-%d %H:%M:%S UTC"),
            day_of_week=now.strftime("%A"),
            current_year=str(now.year),
            history=safe_history,
            message=safe_message,
            understanding=understanding_json,
        )

        # LLM call with one retry
        res: Optional[str] = None
        for attempt in range(1, 3):
            try:
                res = await asyncio.wait_for(
                    self.llm.chat(
                        messages=[{"role": "user", "content": prompt}],
                        model=model,
                        format="json",
                        temperature=0.0,
                    ),
                    timeout=timeout,
                )
                break
            except asyncio.TimeoutError:
                logger.warning("tool_router_llm_timeout", attempt=attempt)
                if attempt == 2:
                    logger.info("tool_router_fallback_triggered", reason="timeout")
                    return ToolRoutingDecision(
                        web_policy=WebSearchPolicy.OPTIONAL_WEB,
                        reasoning="Routing engine timed out — defaulting to optional web.",
                        route_priority=RoutePriority.TASK,
                        confidence=0.3,
                    )
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.warning("tool_router_llm_error", error=str(e), attempt=attempt)
                if attempt == 2:
                    logger.info("tool_router_fallback_triggered", reason="llm_error")
                    return ToolRoutingDecision(
                        web_policy=WebSearchPolicy.OPTIONAL_WEB,
                        reasoning="Routing engine error — defaulting to optional web.",
                        route_priority=RoutePriority.TASK,
                        confidence=0.3,
                    )
                await asyncio.sleep(0.5)

        # Parse JSON response
        try:
            data = json.loads(res)
        except (json.JSONDecodeError, TypeError):
            logger.warning("tool_router_invalid_json", raw=str(res)[:500])
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.OPTIONAL_WEB,
                reasoning="Routing engine returned unparseable output — defaulting to optional web.",
                route_priority=RoutePriority.TASK,
                confidence=0.3,
            )

        # Validate and build decision
        try:
            decision = ToolRoutingDecision(**data)

            if decision.search_queries:
                try:
                    decision.search_queries = _validate_search_queries(decision.search_queries)
                except ValueError as ve:
                    logger.warning("tool_router_search_queries_rejected", reason=str(ve))
                    # Fallback: generate a single clean query from the raw message
                    fallback_q = _build_search_query(message)
                    decision.search_queries = [fallback_q] if fallback_q else None

            logger.info(
                "tool_router_decision",
                intent="llm_evaluated",
                route=decision.route_priority.value,
                web_policy=decision.web_policy.value,
                confidence=decision.confidence,
            )
            return decision

        except Exception as e:
            logger.warning("tool_router_schema_error", error=str(e), raw=str(data)[:500])
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.OPTIONAL_WEB,
                reasoning="Routing engine schema error — defaulting to optional web.",
                route_priority=RoutePriority.TASK,
                confidence=0.3,
            )

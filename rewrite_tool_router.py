import json

content = '''import json
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

_ROUTER_PROMPT = """You are the Tool Routing Engine for LYSTRA.
Your job is to decide whether a web search is required to answer the user's message.

ROUTING PRIORITY
1. Internal LYSTRA identity → NO_WEB, route=IDENTITY
2. Ordinary casual conversation, greetings → NO_WEB, route=CONVERSATION  
3. Personal/emotional sharing → NO_WEB, route=PERSONAL
4. Explaining stable concepts (recursion, sorting) → NO_WEB, route=TASK
5. External/current information needed → MANDATORY_WEB, route=TOOL
6. Deep research requested → DEEP_RESEARCH, route=TOOL

Do not use WEB merely because the user asked a 'what', 'who', 'where' question.
Use WEB only when the answer requires current or external information.
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

Output ONLY a JSON object:
{{
    "web_policy": "MANDATORY_WEB",
    "search_query": "optimized google search string if needed, else null",
    "reasoning": "brief justification",
    "route_priority": "TOOL",
    "confidence": 0.9
}}
"""

_HISTORY_WINDOW = 3

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
            logger.info("tool_router_decision", intent="identity", route="IDENTITY", web_policy="NO_WEB", confidence=1.0)
            return result
            
        # 2. Deep Research check
        if _contains_term(text, DEEP_RESEARCH_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.DEEP_RESEARCH,
                reasoning="Deep research explicitly requested.",
                route_priority=RoutePriority.TOOL,
                confidence=1.0,
                search_query=_build_search_query(message)
            )
            logger.info("tool_router_decision", intent="deep_research", route="TOOL", web_policy="DEEP_RESEARCH", confidence=1.0)
            return result
            
        # 3. Mandatory web check (Moved UP, so recency signals override static explanation prefixes)
        if _contains_term(text, MANDATORY_WEB_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.MANDATORY_WEB,
                reasoning="External/current information required.",
                route_priority=RoutePriority.TOOL,
                confidence=0.95,
                search_query=_build_search_query(message)
            )
            logger.info("tool_router_decision", intent="mandatory_web", route="TOOL", web_policy="MANDATORY_WEB", confidence=0.95)
            return result

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

    async def route(self, message: str, history: list = None, understanding: Any = None) -> ToolRoutingDecision:
        # 1. Deterministic Fast-Path
        decision = self._deterministic_route(message, understanding)
        if decision:
            return decision

        # 2. LLM Evaluation Path
        settings = get_settings()
        try:
            model = settings.TOOL_ROUTING_MODEL
            timeout = settings.TOOL_ROUTING_TIMEOUT_S
        except Exception:
            model = "llama3.2:latest"
            timeout = 5.0

        history = history or []
        history_text = "\\n".join([str(h) for h in history[-_HISTORY_WINDOW:]])
        
        # Security: Escape tags
        safe_history = self._sanitize_for_prompt(history_text)
        safe_message = self._sanitize_for_prompt(message)

        if understanding:
            try:
                understanding_json = understanding.model_dump_json() if hasattr(understanding, "model_dump_json") else str(understanding)
            except Exception:
                understanding_json = "{}"
        else:
            understanding_json = "{}"

        prompt = _ROUTER_PROMPT.format(
            history=safe_history,
            message=safe_message,
            understanding=understanding_json
        )

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
        except asyncio.TimeoutError:
            logger.warning("tool_router_llm_timeout")
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.OPTIONAL_WEB,
                reasoning="Routing engine timed out. Defaulting to optional.",
                route_priority=RoutePriority.TASK,
                confidence=0.3
            )
        except Exception as e:
            logger.warning("tool_router_llm_network_error", error=str(e))
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.OPTIONAL_WEB,
                reasoning="Routing engine network error. Defaulting to optional.",
                route_priority=RoutePriority.TASK,
                confidence=0.3
            )

        try:
            data = json.loads(res)
        except json.JSONDecodeError:
            logger.warning("tool_router_invalid_json", raw_response=res[:500])
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.OPTIONAL_WEB,
                reasoning="LLM returned non-JSON output. Defaulting to optional.",
                route_priority=RoutePriority.TASK,
                confidence=0.3
            )

        try:
            decision = ToolRoutingDecision(**data)
            
            # Security: Even if LLM provides a search query, run it through our deterministic sanitizer
            if decision.search_query:
                decision.search_query = _build_search_query(decision.search_query)
                
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
            return ToolRoutingDecision(
                web_policy=WebSearchPolicy.OPTIONAL_WEB,
                reasoning="Routing engine schema error. Defaulting to optional.",
                route_priority=RoutePriority.TASK,
                confidence=0.3
            )
'''

with open('backend/tools/tool_router.py', 'w', encoding='utf-8') as f:
    f.write(content)

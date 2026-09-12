with open('backend/tools/tool_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Fix A: Add query builder
new_builder = '''_FILLER_PREFIXES = [
    "can you tell me ", "can you find ", "can you check ", "could you tell me ",
    "please tell me ", "please find ", "i want to know ", "i wanna know ",
    "tell me ", "do you know ", "find out ", "let me know ",
]

def _build_search_query(original_message: str) -> str:
    \"\"\"
    Lightweight, zero-latency query cleanup used when we route deterministically
    (i.e. no LLM call was made, so we have no LLM-optimized search_query).
    Strips conversational filler so the raw chat message doesn't go to the
    search API verbatim.
    \"\"\"
    text = original_message.strip()
    lowered = text.lower()
    for prefix in _FILLER_PREFIXES:
        if lowered.startswith(prefix):
            text = text[len(prefix):]
            lowered = text.lower()
    text = text.rstrip("?").strip()
    return text or original_message.strip()

def _contains_term'''

content = content.replace('def _contains_term', new_builder)

# Fix B: Reorder and inject search queries
old_logic = '''        # 2. Stable conceptual explanations check
        if any(text.startswith(prefix) for prefix in STATIC_EXPLANATION_PREFIXES):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Stable conceptual explanation does not require web search.",
                route_priority=RoutePriority.TASK,
                confidence=0.95,
            )
            logger.info("tool_router_decision", intent="stable_explanation", route="TASK", web_policy="NO_WEB", confidence=0.95)
            return result

        # 3. Deep Research check
        if _contains_term(text, DEEP_RESEARCH_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.DEEP_RESEARCH,
                reasoning="Deep research explicitly requested.",
                route_priority=RoutePriority.TOOL,
                confidence=1.0
            )
            logger.info("tool_router_decision", intent="deep_research", route="TOOL", web_policy="DEEP_RESEARCH", confidence=1.0)
            return result
            
        # 4. Mandatory web check
        if _contains_term(text, MANDATORY_WEB_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.MANDATORY_WEB,
                reasoning="External/current information required.",
                route_priority=RoutePriority.TOOL,
                confidence=0.95
            )
            logger.info("tool_router_decision", intent="mandatory_web", route="TOOL", web_policy="MANDATORY_WEB", confidence=0.95)
            return result'''

new_logic = '''        # 2. Deep Research check
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
            
        # 3. Mandatory web check
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
            return result'''

content = content.replace(old_logic, new_logic)

with open('backend/tools/tool_router.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ToolRouter")

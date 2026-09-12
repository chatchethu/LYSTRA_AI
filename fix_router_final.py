with open('backend/tools/tool_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Fix 1: _contains_term regex for boundaries
old_contains = '''def _contains_term(text: str, terms: list[str]) -> bool:
    tokens = set(re.findall(r"[a-z0-9']+", text))
    for term in terms:
        if " " in term:
            if term in text:          # multi-word phrases: substring is fine
                return True
        elif term in tokens:          # single words: exact token match
            return True
    return False'''

new_contains = '''import re
def _contains_term(text: str, terms: list[str]) -> bool:
    tokens = set(re.findall(r"[a-z0-9']+", text))
    for term in terms:
        if " " in term:
            if re.search(r"\\b" + re.escape(term) + r"\\b", text):
                return True
        elif term in tokens:
            return True
    return False'''

content = content.replace(old_contains, new_contains)

# Fix 2: Swap Mandatory Web and Static Explanation
old_routing = '''        # 3. Mandatory web check
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

new_routing = '''        # 3. Stable conceptual explanations check
        if any(text.startswith(prefix) for prefix in STATIC_EXPLANATION_PREFIXES):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="Stable conceptual explanation does not require web search.",
                route_priority=RoutePriority.TASK,
                confidence=0.95,
            )
            logger.info("tool_router_decision", intent="stable_explanation", route="TASK", web_policy="NO_WEB", confidence=0.95)
            return result

        # 4. Mandatory web check
        if _contains_term(text, MANDATORY_WEB_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.MANDATORY_WEB,
                reasoning="External/current information required.",
                route_priority=RoutePriority.TOOL,
                confidence=0.95,
                search_query=_build_search_query(message)
            )
            logger.info("tool_router_decision", intent="mandatory_web", route="TOOL", web_policy="MANDATORY_WEB", confidence=0.95)
            return result'''

content = content.replace(old_routing, new_routing)

# Fix 3: Tag untrusted data in prompt
old_prompt = '''Recent Conversation Context:
{history}

User message: {message}

Semantic Analysis of the User Message:
{understanding}'''

new_prompt = '''Recent Conversation Context:
<untrusted_history>
{history}
</untrusted_history>

User message: <untrusted_message>{message}</untrusted_message>

Semantic Analysis of the User Message:
<semantic_data>
{understanding}
</semantic_data>'''

content = content.replace(old_prompt, new_prompt)

with open('backend/tools/tool_router.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("tool_router.py patched")

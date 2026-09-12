import re

with open('backend/tools/tool_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add search_query to ToolRoutingDecision
content = content.replace('    confidence: float = Field(default=0.9, ge=0.0, le=1.0)', '    confidence: float = Field(default=0.9, ge=0.0, le=1.0)\n    search_query: Optional[str] = None')

# Update Prompt
old_prompt_json = '''{{
    "web_policy": "NO_WEB",
    "reasoning": "brief justification",
    "route_priority": "CONVERSATION",
    "confidence": 0.9
}}'''
new_prompt_json = '''{{
    "web_policy": "MANDATORY_WEB",
    "search_query": "optimized google search string if needed, else null",
    "reasoning": "brief justification",
    "route_priority": "TOOL",
    "confidence": 0.9
}}'''
content = content.replace(old_prompt_json, new_prompt_json)

# Update timeout from 5.0 to 15.0 and change OPTIONAL_WEB fallback to MANDATORY_WEB
content = content.replace('timeout=5.0', 'timeout=15.0')
content = content.replace('web_policy=WebSearchPolicy.OPTIONAL_WEB', 'web_policy=WebSearchPolicy.MANDATORY_WEB')
# Also capture search_query in the route() method
old_return = '''            return ToolRoutingDecision(
                web_policy=WebSearchPolicy(policy_val), 
                reasoning=data.get("reasoning", "Parsed from LLM"),
                route_priority=RoutePriority(route_priority),
                confidence=data.get("confidence", 0.9)
            )'''
new_return = '''            return ToolRoutingDecision(
                web_policy=WebSearchPolicy(policy_val), 
                reasoning=data.get("reasoning", "Parsed from LLM"),
                route_priority=RoutePriority(route_priority),
                confidence=data.get("confidence", 0.9),
                search_query=data.get("search_query")
            )'''
content = content.replace(old_return, new_return)

with open('backend/tools/tool_router.py', 'w', encoding='utf-8') as f:
    f.write(content)

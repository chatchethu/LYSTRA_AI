with open('backend/tools/tool_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Update prompt
old_prompt = '''User message: {message}

Output ONLY a JSON object:'''

new_prompt = '''Recent Conversation Context:
{history}

User message: {message}

Output ONLY a JSON object:'''

content = content.replace(old_prompt, new_prompt)

# Update route signature and usage
old_route = '''    async def route(self, message: str, understanding: Any = None) -> ToolRoutingDecision:
        # Try deterministic routing first
        deterministic = self._deterministic_route(message, understanding)'''

new_route = '''    async def route(self, message: str, understanding: Any = None, history: list = None) -> ToolRoutingDecision:
        # Try deterministic routing first
        deterministic = self._deterministic_route(message, understanding)'''

content = content.replace(old_route, new_route)

old_format = '''            prompt = _ROUTER_PROMPT.format(message=message)'''
new_format = '''            history_text = \"\\n\".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in (history or [])[-3:]])
            prompt = _ROUTER_PROMPT.format(message=message, history=history_text)'''

content = content.replace(old_format, new_format)

# Add USER_IDENTITY_TERMS
old_identity = '''IDENTITY_TERMS = ['''
new_identity = '''USER_IDENTITY_TERMS = [
    "who am i", "my name", "know about me", "do you know me", "about myself", 
    "my details", "remember me", "my preferences", "about me", "know me",
    "what you know about me", "what do you know about me"
]

IDENTITY_TERMS = ['''

content = content.replace(old_identity, new_identity)

# Add USER_IDENTITY_TERMS to deterministic route
old_det = '''        # 1. Identity check first
        if _contains_term(text, IDENTITY_TERMS):'''

new_det = '''        # 1. Identity check first
        if _contains_term(text, USER_IDENTITY_TERMS):
            result = ToolRoutingDecision(
                web_policy=WebSearchPolicy.NO_WEB,
                reasoning="User identity question — answered internally.",
                route_priority=RoutePriority.PERSONAL,
                confidence=1.0
            )
            logger.info("tool_router_decision", intent="user_identity", route="PERSONAL", web_policy="NO_WEB", confidence=1.0)
            return result
            
        if _contains_term(text, IDENTITY_TERMS):'''

content = content.replace(old_det, new_det)

with open('backend/tools/tool_router.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated ToolRouter to use history and check for user identity")

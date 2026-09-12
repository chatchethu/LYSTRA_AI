with open('backend/tools/tool_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_prompt = '''Recent Conversation Context:
{history}

User message: {message}

Output ONLY a JSON object:'''

new_prompt = '''Recent Conversation Context:
{history}

User message: {message}

Semantic Analysis of the User Message:
{understanding}

Output ONLY a JSON object:'''

content = content.replace(old_prompt, new_prompt)

old_format = '''            history_text = "\\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in (history or [])[-3:]])
            prompt = _ROUTER_PROMPT.format(message=message, history=history_text)'''

new_format = '''            history_text = "\\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in (history or [])[-3:]])
            understanding_text = understanding.model_dump_json(indent=2) if understanding else "None"
            prompt = _ROUTER_PROMPT.format(message=message, history=history_text, understanding=understanding_text)'''

content = content.replace(old_format, new_format)

# Tweak the prompt rules to prevent user identity search
old_rules = '''Use WEB only when the answer requires current or external information.'''
new_rules = '''Use WEB only when the answer requires current or external information.
NEVER search the web for questions about the user's personal identity (e.g. 'who am i', 'what is my name', 'do you know me'). This is answered natively from internal DB memory.'''

content = content.replace(old_rules, new_rules)

with open('backend/tools/tool_router.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated ToolRouter LLM to process semantic understanding natively")

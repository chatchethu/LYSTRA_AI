import re
with open("backend/agent/runtime.py", "r", encoding="utf-8") as f:
    text = f.read()

text = re.sub(r'async def process_message.*?\"\"\"', 'async def process_message(\n        self,\n        request: AgentRequest,\n        history: List[Dict[str, str]],\n        state: ConversationState,\n        prefs: UserPreferences,\n        stream_callback=None,\n        is_cancelled_cb=None\n    ) -> Tuple[AgentResponse, ConversationState]:\n        """', text, flags=re.DOTALL)

with open("backend/agent/runtime.py", "w", encoding="utf-8") as f:
    f.write(text)

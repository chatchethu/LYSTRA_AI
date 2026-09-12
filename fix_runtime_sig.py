import re
with open("backend/agent/runtime.py", "r", encoding="utf-8") as f:
    text = f.read()

# Fix the signature
text = re.sub(r'def process_message\(self, request: AgentRequest.*?-> Tuple\[AgentResponse, ConversationState\]:\n', 'def process_message(self, request: AgentRequest, history: List[Dict[str, str]], state: ConversationState, prefs: UserPreferences, stream_callback=None, is_cancelled_cb=None) -> Tuple[AgentResponse, ConversationState]:\n', text, flags=re.DOTALL)
text = re.sub(r'\s*\)\s*->\s*Tuple\[AgentResponse,\s*ConversationState\]:\n', '\n', text)

with open("backend/agent/runtime.py", "w", encoding="utf-8") as f:
    f.write(text)

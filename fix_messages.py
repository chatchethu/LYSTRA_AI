import re

with open('backend/api/messages.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove legacy imports
legacy_imports = [
    "from backend.intelligence.state import ConversationState\n",
    "from backend.intelligence.summarizer import ConversationSummary\n",
    "from backend.intelligence.task_tracker import ActiveTask\n",
    "from backend.intelligence.preferences import UserPreferences\n",
    "from backend.agent.runtime import AgentRuntime\n",
    "from backend.contracts.agent import AgentRequest\n"
]
for li in legacy_imports:
    content = content.replace(li, "")

# Remove the synchronous endpoint block
# It starts at @router.post("/api/v1/messages" and ends before class CancelRequest
pattern = r'@router\.post\("/api/v1/messages".*?(?=from pydantic import BaseModel)'
content = re.sub(pattern, '', content, flags=re.DOTALL)

with open('backend/api/messages.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated messages.py")

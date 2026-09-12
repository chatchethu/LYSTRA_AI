import re

with open('backend/lystra/understanding/semantic_analyzer.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Change retries from 2 to 1 (which means 1 attempt)
content = content.replace('async def analyze(self, message: str, context: Optional[str] = None, retries: int = 2) -> SemanticUnderstanding:', 'async def analyze(self, message: str, context: Optional[str] = None, retries: int = 1) -> SemanticUnderstanding:')

with open('backend/lystra/understanding/semantic_analyzer.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated semantic analyzer retries.")

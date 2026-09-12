with open('backend/lystra/generation/response_strategy.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Add Enums
new_enums = '''from typing import List, Literal, Optional
from pydantic import BaseModel
from backend.lystra.understanding.schemas import SemanticUnderstanding
from enum import Enum

class DepthLevel(str, Enum):
    CONCISE = "concise"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"

class ToneType(str, Enum):
    PROFESSIONAL = "professional"
    WARM = "warm"
    ENERGETIC = "energetic"
    FOCUSED = "focused"
    NEUTRAL = "neutral"
    EMPATHETIC = "empathetic"
    CELEBRATORY = "celebratory"

class EmojiIntensity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class EmojiPurpose(str, Enum):
    ACKNOWLEDGMENT = "acknowledgment"
    EMPATHY = "empathy"
    CELEBRATION = "celebration"
    NONE = "none"

class EmojiStrategy(BaseModel):
    use: bool
    purpose: EmojiPurpose | str
    intensity: EmojiIntensity | str

class ResponseStrategy(BaseModel):
    depth: DepthLevel | str
    tone: ToneType | str
    structure: List[str]
    emoji_strategy: EmojiStrategy'''

# Replace the top imports and models
old_header = '''from typing import List, Literal, Optional
from pydantic import BaseModel
from backend.lystra.understanding.schemas import SemanticUnderstanding

class EmojiStrategy(BaseModel):
    use: bool
    purpose: str
    intensity: Literal["low", "medium", "high"]

class ResponseStrategy(BaseModel):
    depth: Literal["concise", "standard", "comprehensive"]
    tone: Literal["professional", "warm", "energetic", "focused", "neutral", "empathetic", "celebratory"]
    structure: List[str]
    emoji_strategy: EmojiStrategy'''

content = content.replace(old_header, new_enums)

with open('backend/lystra/generation/response_strategy.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated response_strategy.py with Enums")

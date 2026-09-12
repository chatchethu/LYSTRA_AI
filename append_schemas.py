schema_append = """
from datetime import datetime

class PreferenceState(str, Enum):
    ACTIVE = "active"
    UNCERTAIN = "uncertain"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"

class LearnedPreference(BaseModel):
    preference: str
    confidence: float
    source: str
    created_at: datetime
    updated_at: datetime
    evidence_count: int = 1
    state: PreferenceState = PreferenceState.ACTIVE
"""

with open('backend/conversation_intelligence/schemas.py', 'a') as f:
    f.write(schema_append)

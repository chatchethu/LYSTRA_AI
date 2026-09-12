import os

schema_append = """
# ─────────────────────────────────────────────────────────────
# CQ-21 — User-Satisfaction Check
# ─────────────────────────────────────────────────────────────
class SatisfactionScores(BaseModel):
    understanding_score: float = 0.0
    relevance_score: float = 0.0
    naturalness_score: float = 0.0
    depth_fit_score: float = 0.0
    actionability_score: float = 0.0
    specificity_score: float = 0.0

# ─────────────────────────────────────────────────────────────
# CQ-30 — Protected Information Classification
# ─────────────────────────────────────────────────────────────
class ProtectedInfoCategory(str, Enum):
    PUBLIC = "public"
    USER_PROVIDED = "user_provided"
    USER_PRIVATE = "user_private"
    SYSTEM_INTERNAL = "system_internal"
    SECURITY_SENSITIVE = "security_sensitive"
    SECRET = "secret"
    OTHER_USER_PRIVATE = "other_user_private"
"""

with open('backend/conversation_intelligence/schemas.py', 'a') as f:
    f.write(schema_append)

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PrimaryIntent(str, Enum):
    INFORMATION = "information"
    CREATION = "creation"
    TRANSFORMATION = "transformation"
    PLANNING = "planning"
    PROBLEM_SOLVING = "problem_solving"
    EXPLANATION = "explanation"
    COMPARISON = "comparison"
    DECISION_SUPPORT = "decision_support"
    CONVERSATION = "conversation"
    TASK_TOOL_REQUEST = "task_tool_request"


class HierarchicalIntent(BaseModel):
    primary: PrimaryIntent = Field(description="The top-level intent category")

    @field_validator("primary", mode="before")
    def validate_primary(cls, v):
        try:
            return PrimaryIntent(v)
        except ValueError:
            return PrimaryIntent.CONVERSATION

    secondary: str = Field(description="The mid-level category or task intent (e.g. 'summarize', 'extract', 'compare', 'calculate', 'classify', 'locate', 'rewrite', 'translate', 'analyze', 'critique'). Must be inferred semantically, not strictly matched by keywords.")
    tertiary: Optional[str] = Field(None, description="The specific, low-level intent")


class SemanticUnderstanding(BaseModel):
    """
    The full semantic picture of a user turn.
    Produced either by LLMSemanticOutput (happy path) or _fallback_understanding() (error path).
    is_fallback=True signals downstream that the analysis degraded and fields may be defaults.
    """
    goal: str = Field(description="What the user ultimately wants to accomplish")
    intent: HierarchicalIntent = Field(description="The hierarchical intent breakdown")
    topic: Optional[str] = Field("unknown", description="The high-level topic of discussion")
    subtopic: Optional[str] = Field("unknown", description="The specific subtopic")
    entities: List[str] = Field(default_factory=list, description="Key entities (people, places, concepts, technologies) mentioned")
    constraints: List[str] = Field(default_factory=list, description="Explicit constraints or requirements")
    requested_output: Optional[str] = Field(None, description="The format or structure the user expects (e.g. '3 bullet points', 'Python code')")
    urgency: Literal["low", "medium", "high", "critical"] = Field(default="low")
    ambiguity: float = Field(ge=0.0, le=1.0, description="0.0 is perfectly clear, 1.0 is completely ambiguous")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in this semantic understanding")
    context_dependency: float = Field(ge=0.0, le=1.0, description="How much this request relies on previous messages (1.0 = highly dependent)")

    # Emotional and Tone Tracking
    user_emotion: Literal["positive", "neutral", "negative", "frustrated", "confused", "celebratory", "sad", "humorous", "sarcastic"] = Field(default="neutral")
    user_tone: Literal["casual", "formal", "technical", "expressive"] = Field(default="casual")
    subject_sensitivity: Literal["low", "medium", "high"] = Field(
        default="low",
        description="High sensitivity topics (security, medical, loss) strictly suppress emojis and shift tone."
    )

    is_fallback: bool = Field(default=False, description="True if this understanding was generated via fallback due to an error.")
    failure_reason: Optional[str] = Field(None, description="Reason for fallback if is_fallback is True.")


class LLMSemanticOutput(BaseModel):
    """
    Validates ONLY the fields the LLM prompt actually asks for.
    Deliberately NOT a subclass of SemanticUnderstanding — keeping them separate prevents
    Pydantic defaults from silently masking fields the LLM never emitted.
    SemanticAnalyzer.analyze() maps this to a SemanticUnderstanding explicitly.
    """
    goal: str
    intent: HierarchicalIntent
    topic: Optional[str] = "unknown"
    subtopic: Optional[str] = "unknown"
    entities: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    requested_output: Optional[str] = None
    urgency: Literal["low", "medium", "high", "critical"] = "low"
    ambiguity: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    context_dependency: float = Field(ge=0.0, le=1.0)
    user_emotion: Literal["positive", "neutral", "negative", "frustrated", "confused", "celebratory", "sad", "humorous", "sarcastic"] = "neutral"
    user_tone: Literal["casual", "formal", "technical", "expressive"] = "casual"
    subject_sensitivity: Literal["low", "medium", "high"] = "low"

    @field_validator("ambiguity", "confidence", "context_dependency", mode="before")
    def clamp_floats(cls, v):
        try:
            v = float(v)
            return max(0.0, min(1.0, v))
        except (ValueError, TypeError):
            return 0.0

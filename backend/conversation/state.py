from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ConversationMode(str, Enum):
    # New Dynamic Modes
    CASUAL = "casual"
    FOCUSED = "focused"
    SUPPORTIVE = "supportive"
    EXCITED = "excited"
    FRUSTRATED = "frustrated"
    CURIOUS = "curious"
    REFLECTIVE = "reflective"
    PLAYFUL = "playful"
    PROFESSIONAL = "professional"
    
    # Legacy Modes (kept to prevent crashes in older modules during migration)
    TASK = "task"
    TECHNICAL = "technical"
    TEACHING = "teaching"
    PLANNING = "planning"
    RESEARCH = "research"
    SUPPORT = "support"
    CREATIVE = "creative"

class SpeechAct(str, Enum):
    QUESTION = "QUESTION"
    STATEMENT = "STATEMENT"
    COMMAND = "COMMAND"
    CLARIFICATION = "CLARIFICATION"
    ACKNOWLEDGMENT = "ACKNOWLEDGMENT"
    CORRECTION = "CORRECTION"
    UNKNOWN = "UNKNOWN"

class ResponseAction(str, Enum):
    RESPOND = "RESPOND"
    CLARIFY = "CLARIFY"
    EXECUTE_TOOL = "EXECUTE_TOOL"
    SWITCH_GOAL = "SWITCH_GOAL"
    SUMMARIZE = "SUMMARIZE"
    ACKNOWLEDGE = "ACKNOWLEDGE"

class GoalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ABANDONED = "ABANDONED"
    FAILED = "FAILED"
    NONE = "NONE"

class ConversationState(BaseModel):
    # Core Tracking
    active_topic: Optional[str] = None
    previous_topic: Optional[str] = None
    topic_changed: bool = False
    turn_count: int = 0
    
    # Task & Goals
    active_goal: Optional[str] = None
    goal_status: GoalStatus = GoalStatus.ACTIVE
    current_task: Optional[str] = None
    
    # Dialogue Understanding
    speech_act: SpeechAct = SpeechAct.UNKNOWN
    current_entities: List[str] = Field(default_factory=list)
    pending_questions: List[str] = Field(default_factory=list)
    social_intent: Optional[str] = None
    previous_turn_intent: Optional[str] = None
    conversation_stage: str = "casual"
    active_target: str = "none"
    open_issue: Optional[str] = None
    
    # Dynamic Dimensions (New)
    conversation_mode: ConversationMode = ConversationMode.CASUAL
    user_tone: str = "neutral"
    user_verbosity: str = "medium"
    emotion: str = "neutral"
    emotion_intensity: float = 0.0

class AgentState(BaseModel):
    runtime_context: Dict[str, Any] = Field(default_factory=dict)
    session_context: ConversationState = Field(default_factory=ConversationState)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    relevant_memories: List[Any] = Field(default_factory=list)
    future_events: List[Any] = Field(default_factory=list)
    current_topic: Optional[str] = None
    active_goal: Optional[str] = None

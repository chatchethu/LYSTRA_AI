from typing import List, Optional, Dict, Any
import asyncio
import structlog
from pydantic import BaseModel, Field
from backend.lystra.understanding.schemas import SemanticUnderstanding

logger = structlog.get_logger("lystra.conversation_state")

# Maximum number of user constraints kept in memory per conversation.
# Prevents unbounded growth on long sessions. Oldest constraints are evicted first.
_MAX_CONSTRAINTS = 20

# Maximum number of entities tracked per conversation.
_MAX_ENTITIES = 50


class TaskState(BaseModel):
    name: str
    status: str = "pending"
    completed_steps: List[str] = Field(default_factory=list)
    pending_steps: List[str] = Field(default_factory=list)


class ConversationState(BaseModel):
    active_goal: Optional[str] = None
    current_topic: Optional[str] = None
    previous_topic: Optional[str] = None
    user_constraints: List[str] = Field(default_factory=list)
    pending_questions: List[str] = Field(default_factory=list)
    # Fix #3 (entity type): entities are now a list of strings matching SemanticUnderstanding.entities.
    # The old Dict[str, str] was a type mismatch (SemanticUnderstanding.entities is List[str]).
    important_entities: List[str] = Field(default_factory=list)
    # Phase 17: Multi-Turn File Conversation Context
    active_files: List[str] = Field(default_factory=list)
    previous_files: List[str] = Field(default_factory=list)
    user_requested_format: Optional[str] = None
    current_task_state: Optional[TaskState] = None

    # Dynamic styling traits — now wired from understanding (see update_from_understanding)
    # preferred_tone maps from SemanticUnderstanding.user_tone
    preferred_tone: str = "casual"
    # emoji_affinity maps from SemanticUnderstanding.subject_sensitivity:
    #   "low" sensitivity  → "medium" emoji affinity (normal)
    #   "medium" sensitivity → "low" emoji affinity (restrained)
    #   "high" sensitivity  → "none" emoji affinity (suppressed per schema comment)
    emoji_affinity: str = "medium"


def _sensitivity_to_emoji_affinity(sensitivity: str) -> str:
    """Maps subject_sensitivity → emoji_affinity.
    'high' sensitivity topics (medical, legal, security, grief) strictly suppress emojis.
    """
    return {"low": "medium", "medium": "low", "high": "none"}.get(sensitivity, "medium")


class StateManager:
    """
    Per-user conversation state store.

    SCOPING: ExecutionManager._get_state_manager() creates one StateManager per user_id,
    keyed in a dict. This means state is per-user but NOT per-conversation — it persists
    across the user's sessions as long as the process is alive (LRU-evicted at 1000 users).

    PRODUCTION NOTE: For true per-conversation scoping, multi-process safety, and
    crash-survival, back this with a Redis store keyed by (user_id, conversation_id).
    The interface here is designed to make that migration straightforward — every method
    takes `conversation_id` as a parameter, which a Redis-backed implementation would
    use as the key without changing call sites.
    """

    def __init__(self, user_id: str):
        # Fix #1 (session scoping): store the user_id explicitly so ownership is
        # visible in logs and can be asserted by callers. A future Redis-backed
        # implementation would accept conversation_id here as well.
        self.user_id = user_id
        self._state = ConversationState()
        # Fix #7 (concurrency): one lock per StateManager so concurrent turns for the
        # same user can't interleave writes to state fields.
        self._lock = asyncio.Lock()

    async def update_from_understanding(self, understanding: SemanticUnderstanding) -> None:
        """Updates the conversation state based on the latest semantic understanding.

        IMPORTANT: If understanding.is_fallback is True, the update is skipped entirely.
        Fallback understandings contain placeholder junk (goal='Respond to user',
        topic='unknown') — applying them would silently overwrite good state with garbage.
        """
        # Fix #2 (fallback-corruption guard): check is_fallback BEFORE touching any state.
        if getattr(understanding, "is_fallback", False):
            logger.warning(
                "skipping_state_update_fallback",
                user_id=self.user_id,
                reason=getattr(understanding, "failure_reason", None),
            )
            return

        # Fix #5 (input validation): guard against None or wrong type being passed.
        if not isinstance(understanding, SemanticUnderstanding):
            logger.error(
                "skipping_state_update_wrong_type",
                user_id=self.user_id,
                actual_type=type(understanding).__name__,
            )
            return

        async with self._lock:  # Fix #7: serialize concurrent updates
            await self._apply_update(understanding)

    async def _apply_update(self, understanding: SemanticUnderstanding) -> None:
        """Inner update — must be called while holding self._lock."""

        # Fix #1 (previous_topic churn): only shift previous_topic when the topic
        # actually changes. Previously this ran unconditionally, making
        # previous_topic == current_topic after two turns on the same topic.
        if understanding.topic and understanding.topic != "unknown":
            if understanding.topic != self._state.current_topic:
                logger.info(
                    "conversation_topic_changed",
                    user_id=self.user_id,
                    from_topic=self._state.current_topic,
                    to_topic=understanding.topic,
                )
                self._state.previous_topic = self._state.current_topic
                self._state.current_topic = understanding.topic

        if understanding.goal and understanding.goal != "Respond to user":
            if understanding.goal != self._state.active_goal:
                logger.info(
                    "conversation_goal_changed",
                    user_id=self.user_id,
                    from_goal=self._state.active_goal,
                    to_goal=understanding.goal,
                )
                self._state.active_goal = understanding.goal

        # Fix #3 (wire up dead fields): constraints now bounded by _MAX_CONSTRAINTS.
        # Exact-string dedup is preserved; a future improvement would use semantic dedup.
        for c in understanding.constraints:
            if c and c not in self._state.user_constraints:
                self._state.user_constraints.append(c)
                logger.debug("constraint_added", user_id=self.user_id, constraint=c)
        # Evict oldest constraints if cap exceeded
        if len(self._state.user_constraints) > _MAX_CONSTRAINTS:
            evicted = len(self._state.user_constraints) - _MAX_CONSTRAINTS
            self._state.user_constraints = self._state.user_constraints[evicted:]

        if understanding.requested_output:
            self._state.user_requested_format = understanding.requested_output

        # Fix #3 (wire up dead entities field): populate from understanding.entities.
        for entity in understanding.entities:
            if entity and entity not in self._state.important_entities:
                self._state.important_entities.append(entity)
        if len(self._state.important_entities) > _MAX_ENTITIES:
            self._state.important_entities = self._state.important_entities[-_MAX_ENTITIES:]

        # Fix #3 (wire up dead style traits): preferred_tone from user_tone,
        # emoji_affinity derived from subject_sensitivity per the schema docstring.
        if understanding.user_tone:
            self._state.preferred_tone = understanding.user_tone

        if understanding.subject_sensitivity:
            new_affinity = _sensitivity_to_emoji_affinity(understanding.subject_sensitivity)
            if new_affinity != self._state.emoji_affinity:
                logger.debug(
                    "emoji_affinity_changed",
                    user_id=self.user_id,
                    subject_sensitivity=understanding.subject_sensitivity,
                    new_emoji_affinity=new_affinity,
                )
                self._state.emoji_affinity = new_affinity

    def get_state(self) -> ConversationState:
        """Returns a deep copy of the current state.

        Fix #6: previously returned the live mutable object — callers could do
        get_state().user_constraints.append(...) and silently bypass all the
        dedup/cap logic in update_from_understanding. A deep copy prevents that.
        """
        return self._state.model_copy(deep=True)

    def get_state_dict(self) -> Dict[str, Any]:
        """Returns the state as a plain dict for prompt injection."""
        return self.get_state().model_dump()

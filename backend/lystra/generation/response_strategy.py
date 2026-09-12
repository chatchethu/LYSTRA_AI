import structlog
from typing import List, Literal
from pydantic import BaseModel
from backend.lystra.understanding.schemas import SemanticUnderstanding
from enum import Enum

# Fix #1: Use structlog properly so kwargs in logger calls work without throwing TypeError.
logger = structlog.get_logger(__name__)

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
    purpose: EmojiPurpose
    intensity: EmojiIntensity

class ResponseStrategy(BaseModel):
    depth: DepthLevel
    tone: ToneType
    # Fix #8: "structure" here strictly represents formatting tokens (e.g. paragraphs, bullet_points).
    # It does not represent content topics.
    structure: List[str]
    emoji_strategy: EmojiStrategy

def get_default_strategy() -> ResponseStrategy:
    return ResponseStrategy(
        depth=DepthLevel.STANDARD,
        tone=ToneType.NEUTRAL,
        structure=["paragraphs"],
        emoji_strategy=EmojiStrategy(
            use=False,
            purpose=EmojiPurpose.NONE,
            intensity=EmojiIntensity.LOW
        )
    )

class StrategyEngine:
    def determine_strategy(
        self,
        understanding: SemanticUnderstanding,
        state_affinity: Literal["low", "medium", "high"] = "medium"
    ) -> ResponseStrategy:
        """
        Phase 16, 20 & Advanced Emoji Intelligence: Response Strategy Engine.
        Determines depth, tone, structure, and emoji behavior dynamically from semantic intent and emotion.
        """
        # Fix #9: Remove the broad try/except around basic getattr calls.
        intent = getattr(getattr(understanding, "intent", None), "primary", "conversation")
        if hasattr(intent, "value"):
            intent = intent.value

        emotion = getattr(understanding, "user_emotion", "neutral")
        if hasattr(emotion, "value"):
            emotion = emotion.value

        # Fix #2: Correctly extract enum value for sensitivity so the kill-switch works.
        sensitivity = getattr(understanding, "subject_sensitivity", "low")
        if hasattr(sensitivity, "value"):
            sensitivity = sensitivity.value

        if getattr(understanding, "is_fallback", False):
            return get_default_strategy()

        # ── Initial defaults
        depth: DepthLevel = DepthLevel.STANDARD
        tone: ToneType = ToneType.NEUTRAL
        # Default: prose paragraphs for conversational responses.
        # Informational/technical intents override this to structured format below.
        structure: List[str] = ["paragraphs"]
        emoji_use: bool = True
        emoji_purpose: EmojiPurpose = EmojiPurpose.ACKNOWLEDGMENT
        emoji_intensity: EmojiIntensity = EmojiIntensity.LOW

        # ── 1. Intent → strategy mapping (exhaustive) ─
        # Fix #3: Reconciled intent taxonomy with ToolRouter.
        CASUAL_INTENTS = {"conversation", "greeting", "casual_conversation", "small_talk", "farewell", "social"}
        PERSONAL_INTENTS = {"emotional_support", "venting", "complaint", "personal_sharing"}

        if intent in CASUAL_INTENTS:
            depth = DepthLevel.CONCISE
            tone = ToneType.WARM
            structure = ["paragraphs"]  # conversational → prose

        elif intent in PERSONAL_INTENTS:
            depth = DepthLevel.STANDARD
            tone = ToneType.EMPATHETIC
            structure = ["paragraphs"]  # emotional context → prose

        elif intent == "information":
            depth = DepthLevel.STANDARD
            tone = ToneType.NEUTRAL
            # Multi-part informational answer → structured for scannability
            structure = ["headers", "bullet_points"]

        elif intent == "explanation":
            depth = DepthLevel.STANDARD
            tone = ToneType.NEUTRAL
            # Explanations with multiple parts → use bullets/headers to aid clarity
            structure = ["headers", "bullet_points"]

        elif intent == "comparison":
            depth = DepthLevel.STANDARD
            tone = ToneType.NEUTRAL
            # Comparisons are inherently list-like
            structure = ["bullet_points"]

        elif intent == "problem_solving":
            depth = DepthLevel.COMPREHENSIVE
            tone = ToneType.FOCUSED
            emoji_use = False
            # Step-by-step problem solving → numbered/bulleted structure
            structure = ["headers", "bullet_points"]

        elif intent == "creation":
            depth = DepthLevel.COMPREHENSIVE
            tone = ToneType.NEUTRAL
            emoji_use = False
            structure = ["paragraphs"]  # creative output is prose

        elif intent == "transformation":
            depth = DepthLevel.STANDARD
            tone = ToneType.NEUTRAL
            emoji_use = False
            structure = ["paragraphs"]

        elif intent == "planning":
            depth = DepthLevel.COMPREHENSIVE
            tone = ToneType.FOCUSED
            emoji_use = False
            # Plans are always structured with phases/steps
            structure = ["headers", "bullet_points"]

        elif intent == "decision_support":
            depth = DepthLevel.STANDARD
            tone = ToneType.NEUTRAL
            structure = ["bullet_points"]  # options/trade-offs as bullets

        elif intent == "task_tool_request":
            depth = DepthLevel.CONCISE
            tone = ToneType.NEUTRAL
            emoji_use = False
            structure = ["paragraphs"]

        else:
            # Logs if an unknown PrimaryIntent is passed
            logger.warning("unhandled_intent_in_strategy_engine", intent=intent)


        # ── 2. Emotional overrides — run AFTER intent so emotion always wins ─
        pre_override_tone = tone
        pre_override_depth = depth

        if emotion in ("frustrated", "sad"):
            tone = ToneType.EMPATHETIC
            emoji_use = False
            # Fix #4: Step depth down instead of forcing CONCISE unconditionally.
            if depth == DepthLevel.COMPREHENSIVE:
                depth = DepthLevel.STANDARD
            else:
                depth = DepthLevel.CONCISE
                
        elif emotion == "celebratory":
            tone = ToneType.CELEBRATORY
            emoji_use = True
            emoji_purpose = EmojiPurpose.CELEBRATION
            emoji_intensity = EmojiIntensity.HIGH if state_affinity == "high" else EmojiIntensity.MEDIUM
            
        elif emotion == "confused":
            tone = ToneType.WARM
            depth = DepthLevel.CONCISE

        if tone != pre_override_tone or depth != pre_override_depth:
            logger.debug(
                "strategy_emotion_override",
                intent=intent,
                emotion=emotion,
                intent_tone=pre_override_tone,
                final_tone=tone,
                intent_depth=pre_override_depth,
                final_depth=depth,
            )

        # ── 3. Sensitivity kill-switch (runs LAST, trumps tone and emoji) ────────
        # Fix #5: Clarified comment that this overrides tone and emoji, not depth.
        if str(sensitivity).lower() == "high":
            # Fix #6: Reset emoji strategy fields to prevent stale/confusing state.
            emoji_use = False
            emoji_purpose = EmojiPurpose.NONE
            emoji_intensity = EmojiIntensity.LOW
            tone = ToneType.PROFESSIONAL

        try:
            return ResponseStrategy(
                depth=depth,
                tone=tone,
                structure=structure,
                emoji_strategy=EmojiStrategy(
                    use=emoji_use,
                    purpose=emoji_purpose,
                    intensity=emoji_intensity,
                ),
            )
        except Exception as e:
            logger.error("strategy_construction_failed", error=str(e))
            return get_default_strategy()

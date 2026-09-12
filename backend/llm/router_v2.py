import structlog
from typing import Dict, Any, Optional
from backend.config import get_settings

logger = structlog.get_logger(__name__)

class ModelRouterV2:
    """
    Phase 107 & CI-56, CI-57, CI-58: Adaptive Model Router 2.0
    Dynamically routes intents to the most efficient model based on complexity, intent, and context.
    """
    def __init__(self):
        self.settings = get_settings()

    def determine_optimal_model(
        self, 
        prompt: str, 
        task_type: str, 
        context_length: int = 0,
        intent: Optional[str] = None,
        complexity_score: float = 0.5
    ) -> str:
        """Selects the best model considering cost, latency, intent, and complexity."""
        
        # 1. Vision routing
        if task_type == "vision":
            logger.info("router_v2_selected", model=self.settings.OLLAMA_VISION_MODEL, reason="vision_task")
            return self.settings.OLLAMA_VISION_MODEL
            
        # 2. CI-58: Model Routing by Response Strategy / Intent
        # If the task explicitly needs deep reasoning, planning, or coding
        if task_type == "coding" or intent in ["coding", "analysis", "problem_solving", "decision"]:
            logger.info("router_v2_selected", model=self.settings.OLLAMA_CODE_MODEL, reason=f"complex_intent_{intent}")
            return self.settings.OLLAMA_CODE_MODEL
            
        if intent == "planning":
            logger.info("router_v2_selected", model=self.settings.OLLAMA_CODE_MODEL, reason="planning_requires_pro")
            return self.settings.OLLAMA_CODE_MODEL
            
        # 3. CI-56: Response Cost Optimization
        # Use smallest capable model for simple chat
        if intent in ["conversation", "emotional_support", "greeting"]:
            # Could map to a tiny/flash model if configured, but default chat is usually fast
            if complexity_score < 0.3:
                logger.info("router_v2_selected", model=self.settings.OLLAMA_CHAT_MODEL, reason="low_complexity_chat")
                return self.settings.OLLAMA_CHAT_MODEL
            
        # 4. Long Context overflow
        if context_length > 8000:
            logger.info("router_v2_selected", model=self.settings.OLLAMA_CHAT_MODEL, reason="long_context")
            return self.settings.OLLAMA_CHAT_MODEL
            
        # 5. Fallback for general conversational workloads (CI-57 Model Specialization)
        logger.info("router_v2_selected", model=self.settings.OLLAMA_CHAT_MODEL, reason="standard_conversation")
        return self.settings.OLLAMA_CHAT_MODEL


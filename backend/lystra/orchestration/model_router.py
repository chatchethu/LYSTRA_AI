import structlog
from typing import Literal, List, Optional, Dict, Any
from pydantic import BaseModel
from backend.lystra.understanding.schemas import SemanticUnderstanding, PrimaryIntent
from backend.config import get_settings

logger = structlog.get_logger("lystra.model_router")

class RoutingDecision(BaseModel):
    selected_model: str
    reason: str
    requires_vision: bool
    requires_tools: bool
    latency_profile: Literal["fast", "balanced", "heavy"]

# Default capabilities mapping. In a dynamic system, this would be injected via config.
# Fix #6: Avoid hardcoded vendor name string-sniffing by relying on capability flags.
DEFAULT_CAPABILITY_MAP = {
    "llama3.2:latest": {"vision": False, "tools": True, "role": "general"},
    "qwen2.5-coder:32b": {"vision": False, "tools": True, "role": "coder"},
    "qwen2.5-coder": {"vision": False, "tools": True, "role": "coder"},
    "llava:latest": {"vision": True, "tools": False, "role": "vision"},
    # Generic fallback
    "default": {"vision": False, "tools": True, "role": "general"}
}

class ModelRouter:
    # Fix #12: Dependency Injection for defaults makes tests easier and avoids global state
    def __init__(self, 
                 available_models: List[str], 
                 default_model: Optional[str] = None,
                 capability_map: Optional[Dict[str, Dict[str, Any]]] = None):
        self.available_models = available_models
        # Fallback to configured model if none is provided
        self.default_model = default_model or get_settings().OLLAMA_CHAT_MODEL
        self.capability_map = capability_map or DEFAULT_CAPABILITY_MAP

        # Fix #8: Validate that the router has at least one valid model.
        if not self.available_models and not self.default_model:
            raise ValueError("ModelRouter requires at least one available model or a configured default.")

    def _get_capabilities(self, model_name: str) -> Dict[str, Any]:
        """Helper to get capabilities, trying exact match, then substring match, then default."""
        if model_name in self.capability_map:
            return self.capability_map[model_name]
            
        model_lower = model_name.lower()
        for known_model, caps in self.capability_map.items():
            if known_model != "default" and known_model in model_lower:
                return caps
                
        return self.capability_map["default"]

    def get_fallback_model(self, primary_model: str) -> Optional[str]:
        """Returns a fallback model from available_models that is not the primary model."""
        return next((m for m in self.available_models if m != primary_model), None)

    def route(self, understanding: SemanticUnderstanding, context_length: int) -> RoutingDecision:
        """
        Phase 11 & 12: Dynamic Model Routing
        Routes based on primary_intent, context size, and specific tool/vision requirements.
        """
        # Fix #10: Rename 'complexity' to 'primary_intent'
        primary_intent = understanding.intent.primary
        
        # Fix #1: Guard against None in secondary intent
        secondary_intent = (understanding.intent.secondary or "").lower()
        latency: Literal["fast", "balanced", "heavy"] = "balanced"
        
        # Fix #2: Handle entities list correctly. In our schema, entities is List[str].
        # Look for "image" or "vision" in the string representations.
        requires_vision = any("image" in str(e).lower() or "vision" in str(e).lower() for e in (understanding.entities or []))
        
        # Fix #4: Guard against None in context_dependency
        requires_tools = (understanding.context_dependency or 0.0) > 0.8
        
        # Fix #9: Remove the stale/misleading comment.
        base_model = self.available_models[0] if self.available_models else self.default_model
        selected_model = base_model
        
        # Determine base latency / logic constraints
        # Fix #7: Use PrimaryIntent Enum values instead of magic strings
        
        # Phase 47 & 48: Model Routing by Task Modality
        if "spreadsheet" in secondary_intent or "calculate" in secondary_intent or "csv" in secondary_intent:
            requires_tools = True
            latency = "heavy"
        elif primary_intent == PrimaryIntent.COMPARISON or "compare" in secondary_intent or "summarize" in secondary_intent or "reason" in secondary_intent:
            latency = "heavy"
            
        if primary_intent == PrimaryIntent.CONVERSATION and context_length < 2000 and latency != "heavy":
            latency = "fast"
        elif primary_intent in [PrimaryIntent.CREATION, PrimaryIntent.PROBLEM_SOLVING] and "code" in secondary_intent:
            latency = "heavy"
        elif context_length > 30000:
            latency = "heavy"

        # Fix #5: Filter models by capabilities so requires_vision/requires_tools actually gates selection.
        capable_models = []
        for m in (self.available_models or [self.default_model]):
            caps = self._get_capabilities(m)
            # Fix #3: Implicitly fixed by the capabilities map matching (case insensitive lookups)
            if requires_vision and not caps.get("vision", False):
                continue
            if requires_tools and not caps.get("tools", False):
                continue
            capable_models.append((m, caps))

        if capable_models:
            if latency == "heavy" and "code" in secondary_intent:
                # Prioritize a coder model if available among capable models
                coder_model = next((m for m, caps in capable_models if caps.get("role") == "coder"), None)
                selected_model = coder_model if coder_model else capable_models[0][0]
            else:
                selected_model = capable_models[0][0]
        else:
            # If no model matches capabilities, log a warning and fall back to the base model.
            logger.warning("model_router_no_capable_model_found", 
                           requires_vision=requires_vision, requires_tools=requires_tools, 
                           available=self.available_models)
            selected_model = base_model

        reason = (f"intent={primary_intent.value}, secondary={secondary_intent or 'none'}, "
                  f"context_length={context_length}, latency={latency}")

        decision = RoutingDecision(
            selected_model=selected_model,
            reason=reason,
            requires_vision=requires_vision,
            requires_tools=requires_tools,
            latency_profile=latency
        )
        
        # Fix #11: Add observability
        logger.info("routing_decision", 
                    selected_model=decision.selected_model,
                    latency_profile=decision.latency_profile,
                    primary_intent=primary_intent.value,
                    requires_vision=decision.requires_vision,
                    requires_tools=decision.requires_tools,
                    context_length=context_length)
                    
        return decision

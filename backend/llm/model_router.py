from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel
from backend.config import get_settings

settings = get_settings()

class TaskType(str, Enum):
    CHAT = "chat"
    CODE = "code"
    VISION = "vision"
    EMBEDDING = "embedding"
    PLANNING = "planning"
    RESEARCH = "research"
    CREATIVE = "creative"
    ROUTING = "routing"
    DOCUMENT = "document"
    EXTRACTION = "extraction"

class ModelCapability(str, Enum):
    VISION = "vision"
    CODE = "code"
    TOOL_USE = "tool_use"
    FAST = "fast"
    REASONING = "reasoning"

class ModelDef(BaseModel):
    id: str
    version: str
    provider: str
    capabilities: List[ModelCapability]
    context_size: int
    priority: int
    latency_ms_per_token: float
    available: bool = True

class ModelRegistry:
    def __init__(self):
        self.models: Dict[str, ModelDef] = {
            settings.OLLAMA_CHAT_MODEL: ModelDef(
                id=settings.OLLAMA_CHAT_MODEL,
                version="latest",
                provider="ollama",
                capabilities=[ModelCapability.FAST, ModelCapability.TOOL_USE],
                context_size=8192,
                priority=10,
                latency_ms_per_token=10.0,
                available=True
            ),
            settings.OLLAMA_CODE_MODEL: ModelDef(
                id=settings.OLLAMA_CODE_MODEL,
                version="latest",
                provider="ollama",
                capabilities=[ModelCapability.CODE, ModelCapability.REASONING],
                context_size=16384,
                priority=10,
                latency_ms_per_token=15.0,
                available=True
            ),
            settings.OLLAMA_VISION_MODEL: ModelDef(
                id=settings.OLLAMA_VISION_MODEL,
                version="latest",
                provider="ollama",
                capabilities=[ModelCapability.VISION],
                context_size=4096,
                priority=10,
                latency_ms_per_token=25.0,
                available=True
            ),
            settings.OLLAMA_EMBEDDING_MODEL: ModelDef(
                id=settings.OLLAMA_EMBEDDING_MODEL,
                version="latest",
                provider="ollama",
                capabilities=[],
                context_size=8192,
                priority=10,
                latency_ms_per_token=2.0,
                available=True
            )
        }

    def register_model(self, model_def: ModelDef):
        self.models[model_def.id] = model_def

    def get_model(self, model_id: str) -> Optional[ModelDef]:
        return self.models.get(model_id)

class ModelRouter:
    def __init__(self, registry: ModelRegistry = None):
        self.registry = registry or ModelRegistry()

    def get_model(self, task_type: TaskType) -> str:
        if task_type in (TaskType.CODE, TaskType.PLANNING):
            return settings.OLLAMA_CODE_MODEL
        elif task_type == TaskType.VISION:
            return settings.OLLAMA_VISION_MODEL
        elif task_type == TaskType.EMBEDDING:
            return settings.OLLAMA_EMBEDDING_MODEL
        elif task_type == TaskType.DOCUMENT:
            return settings.OLLAMA_CHAT_MODEL
        else:
            return settings.OLLAMA_CHAT_MODEL

    def select_model(self, task_type: TaskType, has_image: bool = False, has_visual_document: bool = False, required_context: int = 0, requires_tools: bool = False) -> str:
        candidates = [m for m in self.registry.models.values() if m.available]

        if has_image or has_visual_document:
            vision_candidates = [m for m in candidates if ModelCapability.VISION in m.capabilities]
            if vision_candidates:
                candidates = vision_candidates

        if task_type in (TaskType.CODE, TaskType.PLANNING):
            code_candidates = [m for m in candidates if ModelCapability.CODE in m.capabilities]
            if code_candidates:
                candidates = code_candidates

        if requires_tools:
            tool_candidates = [m for m in candidates if ModelCapability.TOOL_USE in m.capabilities]
            if tool_candidates:
                candidates = tool_candidates

        if required_context > 0:
            context_candidates = [m for m in candidates if m.context_size >= required_context]
            if context_candidates:
                candidates = context_candidates

        if not candidates:
            return self.get_model(task_type)

        candidates.sort(key=lambda m: (-m.priority, m.latency_ms_per_token))
        return candidates[0].id

    def get_fallback_model(self, failed_model_id: str) -> Optional[str]:
        failed_model = self.registry.get_model(failed_model_id)
        if not failed_model:
            return None
            
        candidates = [m for m in self.registry.models.values() if m.id != failed_model_id and m.available]
        
        if ModelCapability.VISION in failed_model.capabilities:
            vision_candidates = [m for m in candidates if ModelCapability.VISION in m.capabilities]
            if vision_candidates:
                candidates = vision_candidates
        elif ModelCapability.CODE in failed_model.capabilities:
            code_candidates = [m for m in candidates if ModelCapability.CODE in m.capabilities]
            if code_candidates:
                candidates = code_candidates
                
        if not candidates:
            return None
            
        candidates.sort(key=lambda m: (-m.priority, m.latency_ms_per_token))
        return candidates[0].id

    def get_provider_kwargs(self, task_type: TaskType) -> dict:
        kwargs = {}
        if task_type == TaskType.CREATIVE:
            kwargs["temperature"] = 0.8
        elif task_type in (TaskType.CODE, TaskType.PLANNING, TaskType.RESEARCH, TaskType.ROUTING):
            kwargs["temperature"] = 0.1
        else:
            kwargs["temperature"] = 0.5
        return kwargs

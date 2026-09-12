from enum import Enum
from typing import Any, Dict, Optional, List
from pydantic import BaseModel
from abc import ABC, abstractmethod
from uuid import UUID
import structlog

logger = structlog.get_logger(__name__)

class ToolPermissionLevel(str, Enum):
    # Fix #3: Note that this is currently metadata-only and unenforced
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"
    FINANCIAL = "financial"
    COMMUNICATION = "communication"
    SYSTEM = "system"


class ToolRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolResult(BaseModel):
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Dict = {}


class BaseTool(ABC):
    name: str
    description: str
    version: str = "1.0.0"
    permission_level: ToolPermissionLevel = ToolPermissionLevel.READ
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW
    requires_approval: bool = False
    
    @abstractmethod
    def get_schema(self) -> dict:
        """Return the JSON schema for tool input."""
    
    @abstractmethod
    async def execute(self, user_id: UUID, task_id: Optional[UUID] = None, conversation_id: Optional[UUID] = None, request_id: Optional[UUID] = None, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        
    def get_ollama_definition(self) -> dict:
        """Returns the tool definition formatted for Ollama/OpenAI API."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_schema()
            }
        }


class ToolRegistry:
    """Manages available tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._loaded = False
        
    def _auto_register(self):
        # Note: Safe under asyncio without lock, but fragile if threaded
        if self._loaded:
            return
        self._loaded = True
        
        import importlib
        import inspect
        
        try:
            from backend.tools.manifest import TOOL_MODULES
        except ImportError:
            logger.error("tool_manifest_missing", error="backend/tools/manifest.py is required for secure deterministic tool loading")
            TOOL_MODULES = []
        
        for module_name in TOOL_MODULES:
            try:
                module = importlib.import_module(module_name)
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseTool) and obj is not BaseTool:
                        if obj.__module__ == module_name:
                            # Fix #1: Tools instantiated only once
                            instance = obj()
                            tool_name = instance.name
                            
                            # Fix #3: Prevent silent name collisions
                            if tool_name in self._tools:
                                existing_cls = type(self._tools[tool_name]).__name__
                                new_cls = type(instance).__name__
                                logger.error("duplicate_tool_name", name=tool_name, existing=existing_cls, new=new_cls)
                                continue
                                
                            self._tools[tool_name] = instance
                            logger.debug(f"Auto-registered tool: {tool_name}")
            except Exception as e:
                # Fix #2: Silent tool registration failures
                logger.error("tool_registration_failed", module=module_name, error=str(e), exc_info=True)

    def register(self, tool: BaseTool):
        # Fix #3: Check manual registration collisions
        if tool.name in self._tools:
             logger.warning("duplicate_tool_name_overwrite", name=tool.name)
        self._tools[tool.name] = tool
        
    def get_tool(self, name: str) -> Optional[BaseTool]:
        self._auto_register()
        return self._tools.get(name)
        
    def get_all_definitions(self) -> List[dict]:
        self._auto_register()
        return [tool.get_ollama_definition() for tool in self._tools.values()]
        
    def get_all_tools(self) -> List[BaseTool]:
        self._auto_register()
        return list(self._tools.values())

    @property
    def tools(self) -> Dict[str, BaseTool]:
        self._auto_register()
        return self._tools

# Global registry
registry = ToolRegistry()

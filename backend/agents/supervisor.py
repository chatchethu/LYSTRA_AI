from pydantic import BaseModel
from typing import Dict, Any, Optional
import structlog
from backend.agent.runtime import AgentRuntime

logger = structlog.get_logger(__name__)

class SupervisorAgent:
    """
    Phase 96: Multi-Agent System (Supervisor Pattern)
    Delegates complex reasoning to specialists, all sharing the same canonical AgentRuntime core.
    """
    def __init__(self, core_runtime: AgentRuntime):
        self.runtime = core_runtime
        
    async def route_request(self, message: str, understanding=None) -> str:
        """Routes using semantic understanding rather than keywords."""
        if understanding:
            if understanding.intent.primary == "creation" and "code" in understanding.intent.secondary:
                target_specialist = "CodingAgent"
            elif understanding.intent.primary == "information" and understanding.context_dependency > 0.5:
                target_specialist = "ResearchAgent"
            else:
                target_specialist = "GeneralAgent"
        else:
            target_specialist = "GeneralAgent"
            
        logger.info("supervisor_routed", specialist=target_specialist)
        return target_specialist
        
    async def process(self, request_payload: Dict[str, Any]):
        # Identifies the correct agent policy/persona and executes using the core runtime
        target = await self.route_request(request_payload["message"])
        
        # Override policy temporarily based on specialist
        # request_payload["agent_policy"] = get_specialist_policy(target)
        
        # All specialists use the same exact orchestrator, tool gateway, and memory security.
        return await self.runtime.process_message(request_payload)


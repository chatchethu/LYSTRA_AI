"""
Semantic Tool Decision Engine (Phase 20)
Decides between NO_TOOL, MEMORY, WEB, DATABASE using explicit Capability Descriptions,
returning a structured JSON.
"""

from enum import Enum
from pydantic import BaseModel
from typing import List
import json

from backend.llm.gateway import LLMGateway
from backend.llm.model_router import ModelRouter, TaskType

class ToolType(str, Enum):
    NO_TOOL = "NO_TOOL"
    MEMORY = "MEMORY"
    WEB = "WEB"
    DATABASE = "DATABASE"

class ToolDecisionResult(BaseModel):
    tool_required: bool
    selected_tools: List[ToolType]
    reason: str
    confidence: float

class ToolDecisionEngine:
    def __init__(self, llm: LLMGateway, model_router: ModelRouter):
        self.llm = llm
        self.model_router = model_router

    def _build_prompt(self, message: str, information_state: dict, has_relevant_memory: bool) -> str:
        prompt = f"""You are the Semantic Tool Decision Engine.
Your job is to decide which tools are required to fulfill the user's request.

CAPABILITY DESCRIPTIONS:
- MEMORY: Use when the user refers to past conversations, asks about previously discussed topics, or when personal preferences/history are needed.
- WEB: Use when the user asks for up-to-date, real-time, or external factual information that an LLM would not natively know or for which freshness is required.
- DATABASE: Use when the user asks for structured data querying from internal systems.
- NO_TOOL: Use when the LLM can answer the request entirely on its own using its pre-trained knowledge, and no external context is needed.

INFORMATION STATE (deduced from query):
- knowledge_available: {information_state.get('knowledge_available')}
- freshness_required: {information_state.get('freshness_required')}
- external_information_required: {information_state.get('external_information_required')}

Has Relevant Memory context available: {has_relevant_memory}

USER MESSAGE:
"{message}"

Return a JSON object strictly matching this format:
{{
    "tool_required": true/false,
    "selected_tools": ["MEMORY", "WEB", "DATABASE", "NO_TOOL"],
    "reason": "Brief explanation of why these tools were selected",
    "confidence": 0.95
}}

If NO_TOOL is selected, tool_required should be false and selected_tools should be ["NO_TOOL"].
If other tools are selected, tool_required should be true.
Output ONLY valid JSON, no markdown formatting or extra text.
"""
        return prompt

    async def decide_tools(self, message: str, contract: any, has_relevant_memory: bool) -> ToolDecisionResult:
        information_state = getattr(contract, "information_state", {})
        prompt = self._build_prompt(message, information_state, has_relevant_memory)
        
        messages = [{"role": "system", "content": prompt}]
        model = self.model_router.get_model(TaskType.ROUTING)
        kwargs = self.model_router.get_provider_kwargs(TaskType.ROUTING)
        
        response_text = await self.llm.chat(messages, model=model, **kwargs)
        
        # Robust JSON parsing
        try:
            # Clean up markdown block if present
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            
            data = json.loads(cleaned.strip())
            
            # Map robustly to ToolType Enum
            selected_raw = data.get("selected_tools", ["NO_TOOL"])
            selected = []
            for t in selected_raw:
                try:
                    selected.append(ToolType(t))
                except ValueError:
                    pass # ignore unknown tools
            
            if not selected:
                selected = [ToolType.NO_TOOL]
                
            return ToolDecisionResult(
                tool_required=data.get("tool_required", False),
                selected_tools=selected,
                reason=data.get("reason", ""),
                confidence=float(data.get("confidence", 0.0))
            )
        except Exception as e:
            # Fallback based on Information State
            selected = []
            if information_state.get('external_information_required'):
                selected.append(ToolType.WEB)
            if has_relevant_memory:
                selected.append(ToolType.MEMORY)
            
            if not selected:
                selected = [ToolType.NO_TOOL]
                
            return ToolDecisionResult(
                tool_required=(ToolType.NO_TOOL not in selected),
                selected_tools=selected,
                reason="Fallback due to parsing error",
                confidence=0.5
            )

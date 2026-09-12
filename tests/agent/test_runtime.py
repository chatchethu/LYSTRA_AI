import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from backend.contracts.agent import AgentRequest, AgentResponse
from backend.agent.runtime import AgentRuntime
from backend.intelligence.state import ConversationState
from backend.intelligence.preferences import UserPreferences

@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.chat = AsyncMock(return_value={"message": "Mocked LLM response"})
    return llm

@pytest.fixture
def mock_router():
    router = MagicMock()
    router.route_model.return_value = "mock_model"
    return router

@pytest.fixture
def mock_dependencies(monkeypatch):
    # Mock downstream components since we are UNIT testing AgentRuntime
    monkeypatch.setattr("backend.agent.runtime.TurnAnalyzer.analyze_turn", AsyncMock(return_value={"current_intent": "greeting", "current_topic": "general", "emotional_state": "neutral"}))
    monkeypatch.setattr("backend.agent.runtime.MemoryService.retrieve_relevant", AsyncMock(return_value=[]))
    monkeypatch.setattr("backend.agent.runtime.MemoryService.auto_extract_and_store", AsyncMock())
    monkeypatch.setattr("backend.agent.runtime.Planner.create_plan", AsyncMock())
    monkeypatch.setattr("backend.agent.runtime.Executor.execute_step", AsyncMock())

@pytest.mark.asyncio
async def test_runtime_direct_response(mock_llm, mock_router, mock_dependencies):
    runtime = AgentRuntime(db=MagicMock(), llm=mock_llm, model_router=mock_router)
    
    state = ConversationState()
    prefs = UserPreferences()
    
    import uuid
    req = AgentRequest(
        user_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        message="Hello",
        stream=False
    )
    
    resp, new_state = await runtime.process_message(
        request=req,
        history=[],
        state=state,
        prefs=prefs
    )
    
    assert resp.content == "Mocked LLM response"
    assert resp.metadata["action_type"] == "direct_response"
    assert new_state.active_topic == "general"

@pytest.mark.asyncio
async def test_runtime_single_tool(mock_llm, mock_router, monkeypatch):
    monkeypatch.setattr("backend.agent.runtime.TurnAnalyzer.analyze_turn", AsyncMock(return_value={"current_intent": "weather", "current_topic": "weather", "emotional_state": "neutral"}))
    monkeypatch.setattr("backend.agent.runtime.MemoryService.retrieve_relevant", AsyncMock(return_value=[]))
    monkeypatch.setattr("backend.agent.runtime.MemoryService.auto_extract_and_store", AsyncMock())
    monkeypatch.setattr("backend.agent.runtime.registry.execute_tool", AsyncMock(return_value="Tool output"))
    
    runtime = AgentRuntime(db=MagicMock(), llm=mock_llm, model_router=mock_router)
    state = ConversationState()
    prefs = UserPreferences()
    
    import uuid
    req = AgentRequest(
        user_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        message="What is the weather?",
        stream=False
    )
    
    resp, new_state = await runtime.process_message(
        request=req,
        history=[],
        state=state,
        prefs=prefs
    )
    
    assert resp.content == "Mocked LLM response"
    assert resp.metadata["action_type"] == "single_tool"

@pytest.mark.asyncio
async def test_runtime_multi_step(mock_llm, mock_router, monkeypatch):
    monkeypatch.setattr("backend.agent.runtime.TurnAnalyzer.analyze_turn", AsyncMock(return_value={"current_intent": "research", "current_topic": "science", "emotional_state": "neutral"}))
    monkeypatch.setattr("backend.agent.runtime.MemoryService.retrieve_relevant", AsyncMock(return_value=[]))
    monkeypatch.setattr("backend.agent.runtime.MemoryService.auto_extract_and_store", AsyncMock())
    
    # Mock plan execution
    mock_plan = MagicMock()
    mock_plan.steps = []
    monkeypatch.setattr("backend.agent.runtime.AgentRuntime._execute_plan_loop", AsyncMock(return_value=mock_plan))
    monkeypatch.setattr("backend.agent.runtime.Planner.create_plan", AsyncMock(return_value=mock_plan))
    
    runtime = AgentRuntime(db=MagicMock(), llm=mock_llm, model_router=mock_router)
    state = ConversationState()
    prefs = UserPreferences()
    
    import uuid
    req = AgentRequest(
        user_id=uuid.uuid4(),
        conversation_id=uuid.uuid4(),
        message="Research quantum computing.",
        stream=False
    )
    
    resp, new_state = await runtime.process_message(
        request=req,
        history=[],
        state=state,
        prefs=prefs
    )
    
    assert "multi-step task" in resp.content
    assert resp.metadata["action_type"] == "multi_step_task"

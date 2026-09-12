import pytest
import asyncio
from backend.intelligence.state import ConversationState, SpeechAct, GoalStatus
from backend.intelligence.turn_analyzer import TurnAnalyzer
from backend.intelligence.goal_manager import GoalManager
from backend.intelligence.response_decision import ResponseDecisionEngine
from backend.llm.model_router import ModelRouter

class DummyLLM:
    async def chat(self, messages, *args, **kwargs):
        # We can inspect the prompt to return mock json
        prompt = messages[0]["content"]
        if "Turn Analyzer" in prompt:
            return '{"speech_act": "QUESTION", "entities": ["NOVA"], "pending_questions": ["What is NOVA?"]}'
        elif "Goal Manager" in prompt:
            return '{"new_goal": "Learn about NOVA", "goal_status": "ACTIVE", "reasoning": "User asked a direct question"}'
        elif "Decision Engine" in prompt:
            return '{"action": "RESPOND"}'
        return "{}"

@pytest.mark.asyncio
async def test_turn_analyzer():
    llm = DummyLLM()
    router = ModelRouter()
    analyzer = TurnAnalyzer(llm, router)
    
    result = await analyzer.analyze_turn("What is NOVA?", [])
    assert result["speech_act"] == SpeechAct.QUESTION
    assert "NOVA" in result["entities"]
    assert "What is NOVA?" in result["pending_questions"]

@pytest.mark.asyncio
async def test_goal_manager():
    llm = DummyLLM()
    router = ModelRouter()
    manager = GoalManager(llm, router)
    
    state = ConversationState()
    state.speech_act = SpeechAct.QUESTION
    
    result = await manager.update_goal("What is NOVA?", state)
    assert result["active_goal"] == "Learn about NOVA"
    assert result["goal_status"] == GoalStatus.ACTIVE

@pytest.mark.asyncio
async def test_response_decision():
    llm = DummyLLM()
    router = ModelRouter()
    engine = ResponseDecisionEngine(llm, router)
    
    state = ConversationState()
    state.speech_act = SpeechAct.QUESTION
    state.active_goal = "Learn about NOVA"
    state.goal_status = GoalStatus.ACTIVE
    
    action = await engine.decide_action("What is NOVA?", state)
    assert action.name == "RESPOND"

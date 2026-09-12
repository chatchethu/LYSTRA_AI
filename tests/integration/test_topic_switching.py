import pytest
from backend.intelligence.analyzer import ConversationAnalyzer
from backend.intelligence.state import ConversationState

@pytest.mark.asyncio
async def test_topic_switching_bug():
    analyzer = ConversationAnalyzer()
    state = ConversationState()
    history = []
    
    # User: Plan a trip to Goa.
    msg1 = "Plan a trip to Goa."
    contract1, state = analyzer.analyze(msg1, history, state)
    assert contract1.topic == "travel"
    assert contract1.intent == "planning"
    history.append({"role": "user", "content": msg1})
    history.append({"role": "assistant", "content": "Sure, I can help you plan a trip to Goa."})
    
    # User: Write a React login component.
    msg2 = "Write a React login component."
    contract2, state = analyzer.analyze(msg2, history, state)
    assert contract2.topic == "coding"
    assert contract2.intent == "task" # "write" triggers TASK mode
    assert contract2.topic_changed is True
    assert state.task_changed is True
    assert state.previous_topic == "travel"
    assert state.current_topic == "coding"
    history.append({"role": "user", "content": msg2})
    history.append({"role": "assistant", "content": "Here is a React login component."})
    
    # Then: User: Make it TypeScript.
    msg3 = "Make it TypeScript."
    contract3, state = analyzer.analyze(msg3, history, state)
    assert contract3.topic == "coding" # Remains coding
    assert contract3.topic_changed is False
    assert state.task_changed is False
    assert state.current_topic == "coding"
    history.append({"role": "user", "content": msg3})
    history.append({"role": "assistant", "content": "Here it is in TypeScript."})
    
    # Then: User: Continue the Goa trip.
    msg4 = "Continue the Goa trip."
    contract4, state = analyzer.analyze(msg4, history, state)
    assert contract4.topic == "travel"
    assert contract4.topic_changed is True
    assert state.task_changed is True
    assert state.current_topic == "travel"

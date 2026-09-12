"""Tests for topic switching."""
from tests.conftest import analyze
from backend.intelligence.analyzer import ConversationState

def test_travel_to_coding_switch():
    history = []
    contract1, state1 = analyze("Plan a trip to Goa.", history, state=ConversationState())
    assert contract1.topic != "coding"
    
    history.extend([
        {"role": "user", "content": "Plan a trip to Goa."},
        {"role": "assistant", "content": "Here is a plan for Goa..."}
    ])
    
    contract2, state2 = analyze("Write a React component.", history, state1)
    
    assert contract2.topic == "coding"
    assert contract2.topic_changed is True
    assert contract2.previous_topic == contract1.topic

def test_coding_to_planning_switch():
    history = []
    contract1, state1 = analyze("Write a Python script.", history, state=ConversationState())
    assert contract1.topic == "coding"
    
    history.extend([
        {"role": "user", "content": "Write a Python script."},
        {"role": "assistant", "content": "print('hello')"},
    ])
    
    contract2, state2 = analyze("What should I build next for my startup?", history, state1)
    assert contract2.topic == "planning"
    assert contract2.topic_changed is True

def test_short_followup_no_switch():
    history = []
    contract1, state1 = analyze("How do I fix this null exception?", history, state=ConversationState())
    assert contract1.topic == "debugging"
    
    history.extend([
        {"role": "user", "content": "How do I fix this null exception?"},
        {"role": "assistant", "content": "Check for None."},
    ])
    
    contract2, state2 = analyze("what about this?", history, state1)
    assert contract2.topic == "debugging"
    assert contract2.topic_changed is False

def test_explicit_reset():
    history = []
    contract1, state1 = analyze("Write a Python script.", history, state=ConversationState())
    
    history.extend([
        {"role": "user", "content": "Write a Python script."},
        {"role": "assistant", "content": "print('hello')"},
    ])
    
    contract2, state2 = analyze("forget about all of that, let's talk about travel destinations instead.", history, state1)
    assert contract2.topic == "travel"
    assert contract2.topic_changed is True

"""Tests for followups."""
from tests.conftest import analyze
from backend.intelligence.analyzer import ConversationState

def test_followup_retains_topic():
    history = []
    contract1, state1 = analyze("Write a python script", history, state=ConversationState())
    assert contract1.topic == "coding"
    
    history.extend([
        {"role": "user", "content": "Write a python script"},
        {"role": "assistant", "content": "Here is the python code..."}
    ])
    
    contract2, state2 = analyze("make it async", history, state1)
    assert contract2.topic == "coding"
    assert contract2.topic_changed is False

def test_what_about_x():
    history = []
    contract1, state1 = analyze("Explain Docker containers.", history, state=ConversationState())
    assert contract1.topic == "research"
    
    history.extend([
        {"role": "user", "content": "Explain Docker containers."},
        {"role": "assistant", "content": "Docker is a containerization platform."}
    ])
    
    contract2, state2 = analyze("what about kubernetes?", history, state1)
    assert contract2.topic == "research"
    assert contract2.topic_changed is False

def test_multiple_followups():
    history = []
    contract1, state1 = analyze("explain how react works", history, state=ConversationState())
    assert contract1.topic == "coding"
    
    history.extend([
        {"role": "user", "content": "explain how react works"},
        {"role": "assistant", "content": "React is a UI library."}
    ])
    
    contract2, state2 = analyze("what about hooks?", history, state1)
    
    history.extend([
        {"role": "user", "content": "what about hooks?"},
        {"role": "assistant", "content": "Hooks let you use state."}
    ])
    
    contract3, state3 = analyze("how?", history, state2)
    assert contract3.topic == "coding"
    assert contract3.topic_changed is False

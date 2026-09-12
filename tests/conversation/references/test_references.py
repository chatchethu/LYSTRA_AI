"""Tests for reference resolution."""
from tests.conftest import analyze
from backend.intelligence.analyzer import ConversationState

def test_it_reference():
    history = [{"role": "user", "content": "Create a login page."}]
    contract1, state1 = analyze("Create a login page.", history=[], state=ConversationState())
    
    history.extend([
        {"role": "assistant", "content": "Here is the login page."},
        {"role": "user", "content": "Make it darker."}
    ])
    
    contract2, state2 = analyze("Make it darker.", history, state1)
    assert "it" in contract2.references

def test_that_reference():
    history = [{"role": "user", "content": "Create a login page."}]
    contract1, state1 = analyze("Create a login page.", history=[], state=ConversationState())
    
    history.extend([
        {"role": "assistant", "content": "Here is the login page."},
        {"role": "user", "content": "Can you fix that?"}
    ])
    
    contract2, state2 = analyze("Can you fix that?", history, state1)
    assert "that" in contract2.references

def test_make_it_better():
    history = [{"role": "user", "content": "Create a login page."}]
    contract1, state1 = analyze("Create a login page.", history=[], state=ConversationState())
    
    history.extend([
        {"role": "assistant", "content": "Here is the login page."},
        {"role": "user", "content": "make it better"}
    ])
    
    contract2, state2 = analyze("make it better", history, state1)
    assert "it" in contract2.references

def test_fix_this_no_context():
    history = []
    contract1, state1 = analyze("fix this", history, state=ConversationState())
    assert "this" in contract1.references
    assert contract1.ambiguity_score > 0.6

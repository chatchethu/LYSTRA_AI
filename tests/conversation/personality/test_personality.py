"""Tests for personality injection."""
from tests.conftest import analyze, build_system_prompt
from backend.intelligence.analyzer import ConversationState

def test_anti_opener_instructions_present():
    history = []
    contract, state = analyze("What is Docker?", history, state=ConversationState())
    prompt = build_system_prompt(contract)
    
    assert "great question" in prompt.lower()
    assert "certainly" in prompt.lower()
    assert "absolutely" in prompt.lower()
    assert "do not say" in prompt.lower() or "never say" in prompt.lower()

def test_personality_block_present():
    history = []
    contract, state = analyze("What is Docker?", history, state=ConversationState())
    prompt = build_system_prompt(contract)
    
    assert "PERSONALITY:" in prompt

def test_does_not_instruct_to_use_banned_words():
    history = []
    contract, state = analyze("What is Docker?", history, state=ConversationState())
    prompt = build_system_prompt(contract)
    
    # It should not just contain the word in a positive context
    idx = prompt.lower().find("certainly")
    if idx != -1:
        surrounding = prompt.lower()[max(0, idx-60):idx+60]
        assert "not" in surrounding or "avoid" in surrounding or "never" in surrounding

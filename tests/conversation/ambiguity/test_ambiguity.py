"""Tests for ambiguity detection."""
from tests.conftest import analyze
from backend.intelligence.analyzer import ConversationState, RiskLevel

def test_fix_this_ambiguity():
    history = []
    contract, state = analyze("fix this", history, state=ConversationState())
    assert contract.ambiguity_score > 0.6
    assert contract.needs_clarification is True

def test_delete_database_high_risk():
    history = []
    contract, state = analyze("delete the database", history, state=ConversationState())
    assert contract.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    assert contract.needs_clarification is True

def test_clear_request_low_ambiguity():
    history = []
    contract, state = analyze("What is the capital of France?", history, state=ConversationState())
    assert contract.ambiguity_score < 0.3
    assert contract.needs_clarification is False

def test_vague_reference_ambiguity():
    history = []
    contract, state = analyze("make it do the thing", history, state=ConversationState())
    assert contract.ambiguity_score > 0.3
    assert contract.needs_clarification is False

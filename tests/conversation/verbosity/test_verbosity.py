"""Tests for verbosity shaping."""
from tests.conftest import analyze
from backend.intelligence.analyzer import ConversationState, Verbosity, ConversationMode

def test_short_verbosity_for_simple_question():
    history = []
    contract, state = analyze("What is JWT?", history, state=ConversationState())
    assert contract.verbosity == Verbosity.SHORT

def test_detailed_verbosity_for_complex_question():
    history = []
    contract, state = analyze("Explain JWT architecture step by step", history, state=ConversationState())
    assert contract.verbosity in [Verbosity.DETAILED, Verbosity.DEEP]

def test_build_mode_verbosity():
    history = []
    contract, state = analyze("Write a React component for a login page", history, state=ConversationState())
    assert contract.mode == ConversationMode.BUILD
    assert contract.verbosity in [Verbosity.DETAILED, Verbosity.DEEP]

def test_debug_mode_verbosity():
    history = []
    contract, state = analyze("How do I fix this TypeError?", history, state=ConversationState())
    assert contract.mode == ConversationMode.DEBUG
    assert contract.verbosity in [Verbosity.DETAILED, Verbosity.NORMAL]

import pytest
from backend.lystra.understanding.schemas import PrimaryIntent, SemanticUnderstanding
from backend.lystra.generation.response_strategy import StrategyEngine
import structlog

# Suppress structlog output during test to avoid messy logs
structlog.configure(logger_factory=structlog.ReturnLoggerFactory())

def test_all_primary_intents_handled(caplog):
    """
    Fix #10: CI-time schema-drift test.
    Asserts that every member of the PrimaryIntent enum is explicitly
    branched on in StrategyEngine.determine_strategy.
    """
    engine = StrategyEngine()
    
    unhandled_intents = []
    
    for intent_member in PrimaryIntent:
        # Create a mock understanding with this specific intent
        class MockIntent:
            primary = intent_member.value
            
        class MockUnderstanding:
            intent = MockIntent()
            user_emotion = "neutral"
            subject_sensitivity = "low"
            is_fallback = False
            
        understanding = MockUnderstanding()
        
        # Clear log capture before running
        caplog.clear()
        
        # Determine strategy
        engine.determine_strategy(understanding)  # type: ignore
        
        # Check if the unhandled warning was logged
        has_warning = any(
            "unhandled_intent_in_strategy_engine" in rec.message 
            or "unhandled_intent_in_strategy_engine" in getattr(rec, "event", "")
            or getattr(rec, "msg", "") == "unhandled_intent_in_strategy_engine"
            for rec in caplog.records
        )
        
        if has_warning:
            unhandled_intents.append(intent_member.value)
            
    assert not unhandled_intents, f"The following PrimaryIntents are missing explicit branches in StrategyEngine: {unhandled_intents}"

import os
os.environ['SECRET_KEY'] = 'test'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
"""
Shared test fixtures for NOVA AI regression suite.
"""
import sys
sys.path.insert(0, ".")

from backend.intelligence.analyzer import ConversationAnalyzer, ConversationState
from backend.intelligence.prompt_builder import build_system_prompt
from backend.evaluation.runner import run_test
from backend.evaluation.test_cases import ConversationTest, Turn

def make_analyzer():
    return ConversationAnalyzer()

def analyze(message: str, history=None, state=None):
    analyzer = make_analyzer()
    history = history or []
    state = state or ConversationState()
    contract, new_state = analyzer.analyze(message, history, state)
    return contract, new_state
import os
os.environ['SECRET_KEY'] = 'testsecretkey'
os.environ['REDIS_URL'] = 'redis://localhost:6379/0'
os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
os.environ['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'


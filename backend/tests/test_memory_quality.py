import pytest
from datetime import datetime, timezone, timedelta
from backend.lystra.memory.schemas import MemoryObject, MemoryType, MemoryStatus, MemorySource
from backend.lystra.memory.memory_updater import MemoryUpdater
from backend.lystra.orchestration.model_router import ModelRouter, RoutingDecision
from backend.lystra.understanding.schemas import SemanticUnderstanding, HierarchicalIntent, PrimaryIntent

@pytest.fixture
def updater():
    return MemoryUpdater()

def test_memory_expiration(updater):
    # Phase 24 & 36: Memory Expiration Tests
    now = datetime.now(timezone.utc)
    
    # Valid candidate
    mem1 = MemoryObject(user_id='test1', type=MemoryType.PREFERENCE, key='key1', value='val1',
                        status=MemoryStatus.CANDIDATE, confidence=0.5, importance=0.5,
                        updated_at=now - timedelta(days=10), source=MemorySource.INFERRED)
    # Stale candidate
    mem2 = MemoryObject(user_id='test1', type=MemoryType.PREFERENCE, key='key2', value='val2',
                        status=MemoryStatus.CANDIDATE, confidence=0.5, importance=0.5,
                        updated_at=now - timedelta(days=40), source=MemorySource.INFERRED)
    # Expired temporary
    mem3 = MemoryObject(user_id='test1', type=MemoryType.PREFERENCE, key='key3', value='val3',
                        status=MemoryStatus.ACTIVE, confidence=0.9, importance=0.5,
                        expires_at=now - timedelta(days=1), source=MemorySource.EXPLICIT)
                        
    results = updater.expire_stale_memories([mem1, mem2, mem3])
    
    assert results[0].status == MemoryStatus.CANDIDATE
    assert results[1].status == MemoryStatus.EXPIRED
    assert results[2].status == MemoryStatus.EXPIRED

def test_memory_conflicts(updater):
    # Phase 22 & 36: Conflict Resolution
    existing = MemoryObject(user_id='test1', type=MemoryType.PREFERENCE, key='k', value='val1',
                            status=MemoryStatus.ACTIVE, confidence=0.8, importance=0.5,
                            source=MemorySource.INFERRED)
    candidate = MemoryObject(user_id='test1', type=MemoryType.PREFERENCE, key='k', value='val2',
                             status=MemoryStatus.CANDIDATE, confidence=0.8, importance=0.5,
                             source=MemorySource.INFERRED)
                             
    result = updater.resolve_conflict(existing, candidate)
    
    # Both inferred with equal confidence, should update value
    assert result.value == 'val2'
    assert result.previous_value == 'val1'
    assert len(result.metadata.get('history', [])) == 1

def test_instruction_hierarchy():
    # Phase 32 & 36: Ensure hierarchy logic
    pass

def test_model_routing():
    # Phase 35: Routing based on current request context
    router = ModelRouter(available_models=['llama3.2:latest', 'qwen2.5-coder:32b'], default_model='llama3.2:latest')
    
    # Coding intent with heavy context
    intent = HierarchicalIntent(primary=PrimaryIntent.PROBLEM_SOLVING, secondary='code')
    understanding = SemanticUnderstanding(intent=intent, goal="test", ambiguity=0.0, confidence=1.0, context_dependency=0.5)
    
    decision = router.route(understanding, context_length=2000)
    assert decision.latency_profile == 'heavy'
    assert 'qwen' in decision.selected_model.lower()

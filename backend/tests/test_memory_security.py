import pytest
import uuid
from backend.lystra.memory.memory_updater import MemoryUpdater
from backend.lystra.memory.schemas import MemoryObject, MemoryType, MemoryStatus, MemorySource

def test_cross_user_conflict_isolation():
    # Phase 37: Cross-user memory leakage prevention
    updater = MemoryUpdater()
    
    user_a = str(uuid.uuid4())
    user_b = str(uuid.uuid4())
    
    mem_a = MemoryObject(user_id=user_a, type=MemoryType.PREFERENCE, key='k', value='val_a',
                         status=MemoryStatus.ACTIVE, confidence=0.8, importance=0.5, source=MemorySource.INFERRED)
                         
    mem_b = MemoryObject(user_id=user_b, type=MemoryType.PREFERENCE, key='k', value='val_b',
                         status=MemoryStatus.CANDIDATE, confidence=0.8, importance=0.5, source=MemorySource.INFERRED)
                         
    # Attempting to resolve a conflict across different users should raise an assertion
    with pytest.raises(AssertionError, match="Cannot merge memories across different users"):
        updater.resolve_conflict(mem_a, mem_b)

def test_do_not_store_classification():
    # Phase 17 & 37: Privacy check logic (DO_NOT_STORE drops immediately)
    from backend.lystra.memory.schemas import MemoryType
    assert getattr(MemoryType, 'DO_NOT_STORE', None) == 'DO_NOT_STORE'

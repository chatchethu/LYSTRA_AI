import os
import shutil
from pathlib import Path

def cleanup():
    base_dir = Path("backend")
    
    # 1. Delete all __pycache__ and *.pyc
    for p in base_dir.rglob("__pycache__"):
        shutil.rmtree(p, ignore_errors=True)
    
    for p in base_dir.rglob("*.pyc"):
        try:
            p.unlink()
        except:
            pass

    # 2. Files to explicitly remove based on Phase 69
    targets = [
        "evaluation/evaluator.py",
        "orchestration/conversation_engine.py",
        "orchestration/agentic_engine.py",
        "intelligence/context_manager.py",
        "intelligence/memory_manager.py",
        "intelligence/memory_store.py",
        "tools/mock_tasks.py",
        "api/voice.py",
        "files/in_memory_store.py",
        "authorization/in_memory_store.py",
        "prompts/registry.py",  # Old registry
        "response/component_registry.py", # Old registry
    ]
    
    for t in targets:
        target_path = base_dir / t
        if target_path.exists():
            print(f"Deleting deprecated file: {target_path}")
            target_path.unlink()
            
    # 3. Clean temporary debug files
    temp_files = list(Path(".").glob("*.tmp")) + list(Path(".").glob("debug_*.log"))
    for tf in temp_files:
        try:
            tf.unlink()
        except:
            pass
            
    print("Cleanup Phase 69 completed!")

if __name__ == "__main__":
    cleanup()


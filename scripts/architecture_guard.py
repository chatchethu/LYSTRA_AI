import os
import sys
from pathlib import Path
import re

def check_architecture():
    banned_patterns = {
        r"Base\.metadata\.create_all": "Must use alembic migrations in production.",
        r"ConversationEngine": "ConversationEngine is deprecated; use AgentRuntime.",
        r"registry\.execute_tool": "Must execute tools through ToolExecutor to verify permissions.",
        r"_file_store": "In-memory _file_store is deprecated; use PostgreSQL DBFile.",
        r"fake current user": "Fake current user auth stub is banned in production.",
        r"mock response": "Mock responses are not allowed in production code.",
        r"mock token metrics": "Fake TokenUsage metrics are banned (Phase 60).",
        r"return \"Executed planned task\.\"": "Mock string returns are banned.",
        r"return \"Executed tool-based task\.\"": "Mock string returns are banned.",
        r"localhost": "Hardcoded localhost configuration is banned (Phase 70)."
    }
    
    exempt_paths = [
        "backend/tests/",
        "scripts/",
        "docs/",
        "backend/tools/web/ssrf_check.py",
        "backend/multimodal/computer_use.py",
        "backend/config.py"
    ]
    
    violations = []
    
    for py_file in Path("backend").rglob("*.py"):
        if any(exempt.replace("/", "\\") in py_file.as_posix().replace("/", "\\") for exempt in exempt_paths):
            continue
            
        try:
            content = py_file.read_text(encoding="utf-8")
        except Exception:
            continue
            
        for pattern, reason in banned_patterns.items():
            if re.search(pattern, content, re.IGNORECASE):
                violations.append(f"VIOLATION in {py_file}:\n  Reason: {reason}\n  Pattern matched: {pattern}\n")

    if violations:
        print("=== Architecture Guard Violations ===")
        for v in violations:
            print(v)
        sys.exit(1)
    else:
        print("Architecture Guard Passed: No deprecated patterns found.")

if __name__ == "__main__":
    check_architecture()


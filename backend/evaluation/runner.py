"""
Evaluation Runner — LYSTRA AI

Runs all test cases deterministically (no LLM, no network).
Prints pass/fail for each test and a summary score.
"""

from __future__ import annotations

import sys
from typing import Any

# Allow running from project root: python scripts/run_eval.py
sys.path.insert(0, ".")

from backend.evaluation.test_cases import TESTS, ConversationTest, Turn
from backend.intelligence.analyzer import ConversationAnalyzer
from backend.intelligence.state import ConversationState
from backend.intelligence.prompt_builder import build_system_prompt

# ---------------------------------------------------------------------------
# ANSI colours
# ---------------------------------------------------------------------------
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

_BANNED_OPENERS = [
    "certainly!", "certainly,",
    "absolutely!", "absolutely,",
    "great question",
    "of course!",
    "i'd be happy to help",
    "i would be happy",
    "sure thing",
]

_BANNED_CLOSERS = [
    "i hope this helps",
    "let me know if you need",
    "feel free to ask",
    "don't hesitate to",
]


def _check_personality(prompt: str) -> list[str]:
    """
    Verify the system prompt INSTRUCTS the model to avoid robotic patterns.
    The prompt_builder injects these as 'do NOT' rules — we check they're present.
    """
    failures = []
    p_low = prompt.lower()
    # The personality block must contain the key anti-filler instructions
    required_instructions = [
        "great question",       # should appear in "do NOT say" section
        "certainly",            # should appear in "do NOT say" section
        "absolutely",           # should appear in "do NOT say" section
    ]
    for instruction in required_instructions:
        # It should appear but ONLY inside a "do not" / "not say" context
        if instruction in p_low:
            # Check it's in a negative context
            idx = p_low.find(instruction)
            surrounding = p_low[max(0, idx-60):idx+60]
            if "not" not in surrounding and "avoid" not in surrounding and "never" not in surrounding:
                failures.append(
                    f"Personality check: '{instruction}' appears without a 'do not' guard"
                )
        else:
            failures.append(
                f"Personality check: '{instruction}' anti-instruction is missing from system prompt"
            )
    return failures


def _contract_to_dict(contract) -> dict[str, Any]:
    """Flatten contract to simple dict for comparison."""
    return {
        "mode":               contract.mode.value,
        "topic":              contract.topic,
        "topic_changed":      contract.topic_changed,
        "needs_clarification": contract.needs_clarification,
        "risk_level":         contract.risk_level.value,
        "verbosity":          contract.verbosity.value,
        "references":         contract.references,
        "ambiguity_score":    contract.ambiguity_score,
        "user_goal":          contract.user_goal,
    }


def _history_from_turns(turns: list[Turn]) -> list[dict]:
    return [{"role": t.role, "content": t.content} for t in turns]


def run_test(test: ConversationTest, analyzer: ConversationAnalyzer) -> dict:
    """Run a single test. Returns result dict."""
    history = _history_from_turns(test.turns)

    # Build initial state from existing turns
    state = ConversationState()
    for i in range(0, len(test.turns) - 1, 2):
        if i + 1 < len(test.turns):
            _, intermediate_state = analyzer.analyze(
                test.turns[i].content, history[:i], state
            )
            state = intermediate_state

    # Final analysis
    contract, _ = analyzer.analyze(test.final_message, history, state)
    actual = _contract_to_dict(contract)
    system_prompt = build_system_prompt(contract)

    failures = []

    # Check expected fields
    for key, expected_val in test.expected.items():
        actual_val = actual.get(key)
        if key == "references":
            # Check that all expected refs appear
            for ref in expected_val:
                if ref not in (actual_val or []):
                    failures.append(f"Expected reference '{ref}' not found in {actual_val}")
        elif actual_val != expected_val:
            failures.append(f"Field '{key}': expected={expected_val!r}, got={actual_val!r}")

    # Check must_not fields
    for key, not_val in test.must_not.items():
        actual_val = actual.get(key)
        if actual_val == not_val:
            failures.append(f"Field '{key}' must NOT be {not_val!r}, but it is")

    # Special personality check for T07
    if test.id == "T07":
        personality_fails = _check_personality(system_prompt)
        failures.extend(personality_fails)

    return {
        "id":       test.id,
        "name":     test.name,
        "passed":   len(failures) == 0,
        "failures": failures,
        "actual":   actual,
    }


def run_all() -> None:
    analyzer = ConversationAnalyzer()
    results = []

    print(f"\n{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"{BOLD}{CYAN}  LYSTRA AI — Conversation Intelligence Evaluation{RESET}")
    print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

    for test in TESTS:
        result = run_test(test, analyzer)
        results.append(result)

        status = f"{GREEN}PASS{RESET}" if result["passed"] else f"{RED}FAIL{RESET}"
        print(f"  [{status}] {test.id} — {test.name}")

        if not result["passed"]:
            for fail in result["failures"]:
                print(f"         {YELLOW}✗ {fail}{RESET}")
        else:
            # Show key detected values
            a = result["actual"]
            print(f"         {CYAN}mode={a['mode']}  topic={a['topic']}  "
                  f"verbosity={a['verbosity']}  risk={a['risk_level']}{RESET}")

    passed = sum(1 for r in results if r["passed"])
    total  = len(results)
    pct    = int(passed / total * 100)
    colour = GREEN if pct >= 80 else (YELLOW if pct >= 60 else RED)

    print(f"\n{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    print(f"  Result: {colour}{BOLD}{passed}/{total} passed ({pct}%){RESET}")
    print(f"{BOLD}{CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}\n")

    sys.exit(0 if pct == 100 else 1)


if __name__ == "__main__":
    run_all()

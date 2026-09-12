"""
Evaluation Test Cases — LYSTRA AI Conversation Intelligence

10 canonical conversation scenarios with deterministic expected outcomes.
Each test defines the input and what properties of the ConversationContract
must be true for the test to PASS.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Turn:
    role: str   # "user" or "assistant"
    content: str


@dataclass
class ConversationTest:
    id: str
    name: str
    description: str
    turns: list[Turn]                       # full conversation history before the final message
    final_message: str                      # the message being analyzed
    expected: dict[str, Any]               # contract fields that must match
    must_not: dict[str, Any] = field(default_factory=dict)  # contract fields that must NOT match


# ---------------------------------------------------------------------------
# The 10 test cases
# ---------------------------------------------------------------------------

TESTS: list[ConversationTest] = [

    ConversationTest(
        id="T01",
        name="Normal EXPLAIN conversation",
        description="Simple factual question → should be EXPLAIN mode, SHORT verbosity.",
        turns=[],
        final_message="What is Docker?",
        expected={
            "mode": "EXPLAIN",
            "needs_clarification": False,
            "risk_level": "LOW",
        },
    ),

    ConversationTest(
        id="T02",
        name="Topic switch — travel → coding",
        description="User switches from trip planning to React coding. Agent must detect topic_changed=True.",
        turns=[
            Turn("user",      "Plan a trip to Goa."),
            Turn("assistant", "Sure! Here's a 5-day Goa itinerary..."),
        ],
        final_message="Write a React login component.",
        expected={
            "topic_changed": True,
            "topic": "coding",
            "mode": "BUILD",
        },
    ),

    ConversationTest(
        id="T03",
        name="Follow-up retains topic context",
        description="Follow-up question should stay in the same topic as the previous turn.",
        turns=[
            Turn("user",      "Explain PostgreSQL."),
            Turn("assistant", "PostgreSQL is a relational database..."),
        ],
        final_message="What about indexing?",
        expected={
            "topic_changed": False,
        },
    ),

    ConversationTest(
        id="T04",
        name="Reference resolution triggered",
        description='"it" reference after building a login page should be detected.',
        turns=[
            Turn("user",      "Create a login page."),
            Turn("assistant", "Here's a login page component..."),
        ],
        final_message="Make it darker.",
        expected={
            "references": ["it"],
            "topic_changed": False,
        },
    ),

    ConversationTest(
        id="T05",
        name="Ambiguous message — needs clarification",
        description='Short vague message with no prior context → high ambiguity, needs clarification.',
        turns=[],
        final_message="Fix this.",
        expected={
            "needs_clarification": True,
        },
    ),

    ConversationTest(
        id="T06",
        name="Goal understanding — performance",
        description='"My app is too slow" should be performance/debug mode, not generic explain.',
        turns=[],
        final_message="My app is too slow.",
        expected={
            "mode": "DEBUG",
        },
        must_not={
            "mode": "EXPLAIN",
        },
    ),

    ConversationTest(
        id="T07",
        name="Personality — no banned openers",
        description="Test that the prompt builder does NOT inject banned opener phrases.",
        turns=[],
        final_message="What is Redis?",
        expected={
            "mode": "EXPLAIN",
        },
        # Evaluated separately via prompt content check in runner
    ),

    ConversationTest(
        id="T08a",
        name="Verbosity SHORT — simple question",
        description="Simple one-line question → SHORT verbosity.",
        turns=[],
        final_message="What is JWT?",
        expected={
            "verbosity": "SHORT",
        },
    ),

    ConversationTest(
        id="T08b",
        name="Verbosity DETAILED — complex question",
        description="Complex architecture question → DETAILED verbosity.",
        turns=[],
        final_message="Explain JWT authentication architecture and show me how to implement it in FastAPI.",
        expected={
            "verbosity": "DETAILED",
        },
    ),

    ConversationTest(
        id="T09",
        name="Dangerous action — confirmation required",
        description="Delete database command → HIGH risk, needs_clarification=True.",
        turns=[],
        final_message="Delete the database.",
        expected={
            "needs_clarification": True,
            "risk_level": "HIGH",
        },
    ),

    ConversationTest(
        id="T10",
        name="Conversation reset intent",
        description='"Forget what we were discussing" → topic switch + reset.',
        turns=[
            Turn("user",      "Plan a trip to Goa."),
            Turn("assistant", "Here's a 5-day Goa itinerary..."),
        ],
        final_message="Forget what we were discussing. Let's talk about GPUs.",
        expected={
            "topic_changed": True,
        },
    ),
]

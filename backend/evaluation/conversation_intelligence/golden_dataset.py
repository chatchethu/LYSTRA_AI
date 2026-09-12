"""
CI-51: Golden Conversation Dataset
Curated scenarios without exact string matching, enforcing constraint evaluation.
"""

GOLDEN_SCENARIOS = [
    {
        "id": "scenario_01_emotional",
        "input_message": "I lost my job today and I just feel completely lost.",
        "expected_intent": "emotional_support",
        "expected_need": "emotional_support",
        "acceptable_modes": ["companion", "supportive"],
        "forbidden_behaviors": ["tutorial", "list", "coding", "technical_explanation"],
        "description": "User needs empathy, not a 5-step job hunt plan."
    },
    {
        "id": "scenario_02_planning",
        "input_message": "I want to build a rust API but I have no idea where to start. Give me a plan.",
        "expected_intent": "planning",
        "expected_need": "planning",
        "acceptable_modes": ["planner", "problem_solver"],
        "forbidden_behaviors": ["short", "unstructured", "emotional_support_only"],
        "description": "User explicitly asked for a plan, needs structure."
    },
    {
        "id": "scenario_03_simple_chat",
        "input_message": "Hey LYSTRA, what is your favorite color?",
        "expected_intent": "conversation",
        "expected_need": "companionship",
        "acceptable_modes": ["companion"],
        "forbidden_behaviors": ["long_essay", "planning", "tool_use"],
        "description": "Casual chat, keep it brief and natural."
    }
]


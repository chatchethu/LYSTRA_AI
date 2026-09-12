# NOVA Conversation Intelligence Dashboard

## Core Accuracy Metrics
* **Intent Accuracy**: Tracked via `observability.py` (Expected vs Detected)
* **Need Accuracy**: Monitored post-turn matching User Need schema.
* **Topic Accuracy**: Real-time Topic Graph divergence tracking.
* **Mode Accuracy**: Companion/Planner/Analyst alignment tracking.

## Quality & Health Metrics
* **Response Quality**: 0.0 - 1.0 Aggregate scored via CI-Evaluator.
* **User Satisfaction**: Derived from explicit `FeedbackAction` triggers (Thumbs Up/Down).
* **Regeneration Rate**: Percentage of turns the user clicks "Regenerate".
* **Clarification Rate**: How often the CI Engine triggers `ClarificationDecision.ASK_QUESTION`.

## Response Profiling
* **Average Response Length**: Token counts per turn to prevent long-essay creep.
* **Overlong Response Rate**: Alerts if the engine consistently violates the brevity policy.
* **Generic Response Rate**: Tracked via `ResponseDiversityEngine` duplication alerts.
* **Repetition Rate**: How often identical questions or phrases slip through.
* **Task Success Rate**: Mapped via `TopicTaskRegistry` when a task moves from open -> complete.


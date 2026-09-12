from typing import Optional, List
import structlog
import json
import asyncio
import random
from pydantic import ValidationError
from backend.llm.gateway import LLMGateway
from backend.lystra.understanding.schemas import (
    SemanticUnderstanding,
    HierarchicalIntent,
    PrimaryIntent,
    LLMSemanticOutput,
)
from backend.config import get_settings

logger = structlog.get_logger("lystra.semantic_analyzer")


class SemanticAnalyzer:
    def __init__(self, llm_gateway: LLMGateway):
        self.llm = llm_gateway
        self.settings = get_settings()

    def _get_system_prompt(self) -> str:
        valid_primaries_str = " | ".join(f'"{i.value}"' for i in PrimaryIntent)
        return f"""You are LYSTRA's semantic understanding engine.
Analyze the user's message and determine the deep semantic meaning, goal, and constraints.
Do NOT rely on mere keywords. Understand what they actually want.

INTENT CLASSIFICATION GUIDE — choose the single best match:
- "conversation": greetings, small talk, social messages, personal check-ins (e.g. "Hello", "How are you", "Thanks", "Who are you")
- "information": factual questions expecting a direct answer (e.g. "What is the capital of India?", "Who invented X?")
- "explanation": understanding how/why something works (e.g. "How does X work?", "Why does Y happen?")
- "comparison": comparing two or more options (e.g. "X vs Y", "difference between A and B")
- "problem_solving": debugging errors, fixing issues, troubleshooting (e.g. "My code throws X error", "This isn't working")
- "creation": generating new content (e.g. "Write a poem", "Draft an email", "Create a plan")
- "transformation": reformatting or modifying existing content (e.g. "Summarise this", "Translate this", "Rewrite this")
- "planning": creating multi-step strategies or roadmaps (e.g. "Plan my week", "How do I start learning X?")
- "decision_support": helping choose between options (e.g. "Should I use X or Y?", "Which is better?")
- "task_tool_request": requesting tool use (e.g. "Search for X", "Look up Y")

IMPORTANT: Simple or short messages are almost always "conversation" or "information".
Only use "problem_solving" if there is an actual error, bug, or broken system to fix.

EMOTION GUIDE: Reflect the actual emotional register of the message.
- "frustrated": the user sounds annoyed, stuck, or fed up
- "confused": the user seems lost or uncertain
- "sad": the user is expressing grief, loss, or low mood
- "celebratory": the user is excited, happy, sharing good news
- "humorous": the user is joking or playful
- "sarcastic": the user is using irony or mock-seriousness
- "neutral": default for most informational or task messages

SENSITIVITY GUIDE: Set subject_sensitivity to "high" for topics involving medical conditions,
legal issues, security vulnerabilities, financial distress, grief, or personal trauma.
Set "medium" for health advice, relationships, or political topics.
Set "low" for technical, creative, or general knowledge questions.

URGENCY GUIDE: "critical" = time-sensitive emergency. "high" = user needs this right now.
"medium" = moderate priority. "low" = general request with no time pressure.

CONVERSATION CONTEXT RULES — read this carefully:
The "Recent Context" provided includes the last few messages in [{{"role": ..., "content": ...}}] format.
role="user" = what the user said. role="assistant" = what you (LYSTRA) previously replied.

Use this context to resolve ambiguous or short messages:
- If the user's current message is short and emotional (e.g. "I'm worried", "what should I do", "I'm scared"),
  look at the previous conversation to understand WHAT they are worried/scared about.
  Set the topic/goal based on the prior conversation's subject, NOT the current message alone.
  Set context_dependency HIGH (0.8+) and intent to "emotional_support" or "conversation".
- If the user's message is a follow-up to a complex assistant response (like a study plan, code, or advice),
  treat it as continuing that topic — don't classify it as unknown.
- NEVER classify a clearly emotional follow-up message as "invalid_input" or "unknown topic".
  Even if the spelling is imperfect, infer intent from context.
- Short messages like "ok", "then what", "and then", "what next", "what should i do" after a detailed
  assistant reply should be classified as "conversation" with high context_dependency, NOT as ambiguous.

Output MUST be strictly valid JSON matching this schema exactly:
{{
  "goal": "string — what the user wants to accomplish",
  "intent": {{
    "primary": {valid_primaries_str},
    "secondary": "string — finer category e.g. 'technical', 'personal'"
  }},
  "topic": "string — high-level topic",
  "subtopic": "string — specific subtopic",
  "entities": ["list of key entities, technologies, or people mentioned — empty list if none"],
  "constraints": ["list of explicit constraints or requirements — empty list if none"],
  "requested_output": null,
  "urgency": "low" | "medium" | "high" | "critical",
  "ambiguity": <float 0.0-1.0>,
  "confidence": <float 0.0-1.0>,
  "context_dependency": <float 0.0-1.0>,
  "user_emotion": "positive" | "neutral" | "negative" | "frustrated" | "confused" | "celebratory" | "sad" | "humorous" | "sarcastic",
  "user_tone": "casual" | "formal" | "technical" | "expressive",
  "subject_sensitivity": "low" | "medium" | "high"
}}
Only output the JSON object. No markdown fences, no prose."""

    async def analyze(self, message: str, recent_context: Optional[List[dict]] = None) -> SemanticUnderstanding:
        # NOTE: message[:50] preview is logged at info level — review against your
        # data-handling policy if user messages may contain PII.
        logger.info("semantic_analysis_started", message_preview=message[:50])

        # Guard limits
        message = message[:4000]
        context_json = json.dumps(recent_context[-5:] if recent_context else [], ensure_ascii=False)
        prompt = f"Recent Context:\n{context_json}\n\nUser Message:\n{message}"

        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": prompt},
        ]

        max_attempts = 2
        # Bound early so exception handlers are never NameError if the variables
        # are referenced before the assignment inside the try block.
        clean_text = ""
        data: dict = {}

        for attempt in range(1, max_attempts + 1):
            try:
                response_text = await asyncio.wait_for(
                    self.llm.chat(messages, temperature=0.1),
                    timeout=self.settings.SEMANTIC_ANALYSIS_TIMEOUT_S,
                )

                clean_text = response_text.replace("```json", "").replace("```", "").strip()
                start_idx = clean_text.find("{")
                end_idx = clean_text.rfind("}")

                # Explicit log for the "model returned no JSON at all" case —
                # distinguishable from "found JSON but malformed" in production traces.
                if start_idx == -1 or end_idx == -1:
                    logger.warning(
                        "semantic_analysis_no_json_found",
                        attempt=attempt,
                        raw_preview=clean_text[:200],
                    )
                    if attempt == max_attempts:
                        return self._fallback_understanding(reason="no_json_in_response")
                    # Exponential backoff with jitter before retrying
                    backoff = min(2 ** (attempt - 1), 8) + random.uniform(0, 1)
                    await asyncio.sleep(backoff)
                    continue

                clean_text = clean_text[start_idx : end_idx + 1]
                data = json.loads(clean_text)

                # LLMSemanticOutput validates ONLY the fields the prompt asked for.
                # It is intentionally NOT a subclass of SemanticUnderstanding — that
                # separation prevents Pydantic defaults from silently masking un-emitted
                # fields (which would make emotion/sensitivity routing permanently dead code).
                validated_model = LLMSemanticOutput.model_validate(data)

                # Explicit field-by-field mapping: every field that flows from LLM output
                # into SemanticUnderstanding is named here. This means a future field
                # addition to SemanticUnderstanding raises immediately rather than
                # silently taking a default that hides the gap.
                return SemanticUnderstanding(
                    goal=validated_model.goal,
                    intent=validated_model.intent,
                    topic=validated_model.topic,
                    subtopic=validated_model.subtopic,
                    entities=validated_model.entities,
                    constraints=validated_model.constraints,
                    requested_output=validated_model.requested_output,
                    urgency=validated_model.urgency,
                    ambiguity=validated_model.ambiguity,
                    confidence=validated_model.confidence,
                    context_dependency=validated_model.context_dependency,
                    user_emotion=validated_model.user_emotion,
                    user_tone=validated_model.user_tone,
                    subject_sensitivity=validated_model.subject_sensitivity,
                    is_fallback=False,
                    failure_reason=None,
                )

            except json.JSONDecodeError as e:
                # JSON errors typically mean the model returned prose instead of JSON.
                # Not worth retrying — the same malformed response is unlikely to fix itself.
                logger.warning(
                    "semantic_analysis_json_error",
                    error=str(e),
                    output_preview=clean_text[:300],
                )
                return self._fallback_understanding(reason="json_decode_error")

            except ValidationError as e:
                # Log the raw intent value separately so we can track model drift
                # (hallucinated enum values) vs structural malformation in dashboards.
                raw_intent = (
                    data.get("intent", {}).get("primary") if isinstance(data, dict) else None
                )
                logger.warning(
                    "semantic_analysis_validation_error",
                    error=str(e),
                    raw_intent=raw_intent,
                )
                return self._fallback_understanding(reason="schema_validation_error")

            except asyncio.TimeoutError:
                logger.warning(
                    "semantic_analysis_timeout",
                    attempt=attempt,
                    max_attempts=max_attempts,
                )
                if attempt == max_attempts:
                    return self._fallback_understanding(reason="timeout")
                # Exponential backoff with jitter between timeout retries.
                backoff = min(2 ** (attempt - 1), 8) + random.uniform(0, 1)
                await asyncio.sleep(backoff)

            except Exception as e:
                # Intentionally broad: the LLM gateway raises heterogeneous provider
                # exceptions (connection errors, SSL errors, Ollama-specific errors)
                # that don't share a common base class yet. Narrow this once gateway-
                # specific exceptions are formally defined in backend/llm/exceptions.py.
                logger.warning(
                    "semantic_analysis_llm_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    attempt=attempt,
                )
                if attempt == max_attempts:
                    return self._fallback_understanding(reason="llm_network_error")
                backoff = min(2 ** (attempt - 1), 8) + random.uniform(0, 1)
                await asyncio.sleep(backoff)

        # Post-loop safety net — should be unreachable given the explicit returns above,
        # but guarantees the declared return type contract is never violated if a future
        # refactor introduces a new exception type without a return on the final attempt.
        return self._fallback_understanding(reason="max_attempts_exhausted")

    def _fallback_understanding(self, reason: str) -> SemanticUnderstanding:
        """Returns a safe, structurally complete SemanticUnderstanding for any failure path.
        All fallback paths produce the same field structure as the happy path,
        so downstream consumers don't need to special-case missing fields.
        """
        return SemanticUnderstanding(
            goal="Respond to user",
            intent=HierarchicalIntent(
                primary=PrimaryIntent.CONVERSATION,
                secondary="casual",
                tertiary=None,
            ),
            topic="unknown",
            subtopic="unknown",
            entities=[],
            constraints=[],
            requested_output=None,
            urgency="low",
            ambiguity=0.0,
            confidence=0.0,
            context_dependency=0.0,
            user_emotion="neutral",
            user_tone="casual",
            subject_sensitivity="low",
            is_fallback=True,
            failure_reason=reason,
        )

import json
import asyncio
import structlog
from pydantic import BaseModel, Field
from backend.config import get_settings

logger = structlog.get_logger(__name__)

class QualityMetrics(BaseModel):
    """
    Phase 29: Self-Evaluation Without Exposing Internal Reasoning
    """
    relevance: float = Field(ge=0.0, le=1.0)
    completeness: float = Field(ge=0.0, le=1.0)
    grounding: float = Field(ge=0.0, le=1.0)
    instruction_following: float = Field(ge=0.0, le=1.0)
    format_quality: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Fix #1: Explicit signal of evaluation success vs failure
    evaluation_succeeded: bool = Field(default=True)

class QualityEvaluator:
    def __init__(self, llm_gateway):
        self.llm = llm_gateway

    async def evaluate(self, generated_response: str, request_goal: str, file_context: str = "") -> QualityMetrics:
        """Evaluates the generated answer to produce quality signals."""
        prompt = f"Goal: {request_goal}\nResponse: {generated_response}"
        system = "Evaluate the quality of this response on a 0.0 to 1.0 scale. Output only valid JSON matching this schema: {'relevance': 0.0, 'completeness': 0.0, 'grounding': 0.0, 'instruction_following': 0.0, 'format_quality': 0.0, 'confidence': 0.0}"
        
        # Phase 22: Document Answer Grounding
        if file_context:
            system += (
                "\n\nCRITICAL GROUNDING CHECK (Phase 22): Since this request involves a document, rigidly evaluate the 'grounding' metric. "
                "Check: Does the answer come from the file? Did it invent a value? Did it mix unrelated sections? "
                "Did it confuse sheets/pages? If any evidence is fabricated or insufficient, score 'grounding' below 0.5. "
                "If it honestly states evidence is insufficient, score 'grounding' high (e.g. 1.0) because it avoided fabrication."
            )
        
        response_text = None  # Fix #2: Initialize safely before try block
        try:
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]
            
            # Fix #3: Add explicit timeout for the evaluator's LLM call
            response_text = await asyncio.wait_for(
                self.llm.chat(messages, temperature=0.1),
                timeout=500.0
            )
            
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            
            data = json.loads(clean_text)
            
            # Fix #4: Validate JSON shape before unpacking
            if not isinstance(data, dict):
                raise ValueError(f"Expected JSON object, got {type(data).__name__}")
                
            return QualityMetrics(**data)
        except Exception as e:
            # Fix #1: Log loudly and return deliberate fail-open values with evaluation_succeeded=False
            logger.error("quality_evaluation_failed", error=str(e), raw_response=(response_text or "")[:500])
            return QualityMetrics(
                relevance=0.5, completeness=0.5, grounding=0.5, 
                instruction_following=0.5, format_quality=0.5, confidence=0.0,
                evaluation_succeeded=False
            )
            
    def requires_revision(self, metrics: QualityMetrics) -> bool:
        # If evaluation failed entirely, fail-open (do not require revision).
        if not metrics.evaluation_succeeded:
            return False
            
        # Fix #5: Use settings-driven threshold
        threshold = getattr(get_settings(), "QUALITY_REVISION_THRESHOLD", 0.85)
        
        # We only check relevance, grounding, and instruction_following because these are
        # the critical factors for safety and correctness. Completeness and format_quality
        # are informational and shouldn't trigger an expensive revision loop on their own.
        return any(score < threshold for score in [
            metrics.relevance, metrics.grounding, metrics.instruction_following
        ])

import json
import logging
import os
from datetime import datetime
from pydantic import BaseModel
from typing import List, Literal, Optional

# Phase 32 & 33: Strict isolation of telemetry for offline evaluation
TELEMETRY_LOG_FILE = os.path.join(os.getcwd(), 'offline_eval_logs', 'telemetry.jsonl')
os.makedirs(os.path.dirname(TELEMETRY_LOG_FILE), exist_ok=True)

telemetry_logger = logging.getLogger("offline_telemetry")
telemetry_logger.setLevel(logging.INFO)
fh = logging.FileHandler(TELEMETRY_LOG_FILE)
telemetry_logger.addHandler(fh)

class FeedbackEvent(BaseModel):
    timestamp: str
    user_id: str
    feedback_text: str
    classification: Literal[
        "correct", "incorrect", "incomplete", "too long", "too short", 
        "misunderstood request", "wrong file section", "wrong calculation", 
        "wrong tone", "wrong formatting", "irrelevant memory", "excessive personalization", "unknown"
    ]
    source: Literal["explicit", "implicit"]
    
class TelemetryPipeline:
    '''
    Phase 33 & 34: Learning Loop & Feedback Classification
    Logs anonymized/structured events for offline evaluation and prompt improvements.
    Does NOT modify live production behavior (Phase 32).
    '''
    def __init__(self, llm_gateway):
        self.llm = llm_gateway
        
    async def classify_and_log_feedback(self, user_id: str, feedback: str, source: str):
        prompt = f'''Classify the following user feedback into exactly ONE of these categories:
- correct
- incorrect
- incomplete
- too long
- too short
- misunderstood request
- wrong file section
- wrong calculation
- wrong tone
- wrong formatting
- irrelevant memory
- excessive personalization
- unknown

Feedback: "{feedback}"
Return JSON: {{"classification": "<category>"}}
'''
        try:
            messages = [{"role": "system", "content": "You are a telemetry classifier."}, {"role": "user", "content": prompt}]
            resp = await self.llm.chat(messages, temperature=0.1)
            
            clean = resp.replace("`json", "").replace("`", "").strip()
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start != -1 and end != 0:
                data = json.loads(clean[start:end])
                classification = data.get("classification", "unknown")
                
                event = FeedbackEvent(
                    timestamp=datetime.utcnow().isoformat(),
                    user_id=user_id,
                    feedback_text=feedback,
                    classification=classification,
                    source=source
                )
                telemetry_logger.info(event.model_dump_json())
        except Exception as e:
            # Fail silently to not disrupt prod
            pass

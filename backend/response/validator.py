"""
Schema Validator — LYSTRA Dynamic Response System
Phase 21: Validates generated JSON blocks before sending to the frontend.
"""

import json
from typing import Dict, Any

class ResponseValidator:
    """
    Validates LLM output against the JSON block schema.
    If it fails, it can attempt a repair.
    """
    
    @staticmethod
    def validate_and_repair(raw_output: str) -> Dict[str, Any]:
        """
        Attempts to parse the raw text as JSON.
        If the LLM wrapped it in markdown, strips the markdown.
        If it's completely invalid, wraps the raw text in a generic 'text' block.
        """
        text = raw_output.strip()
        
        # Strip markdown if present
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        try:
            parsed = json.loads(text)
            if "blocks" in parsed and isinstance(parsed["blocks"], list):
                # Valid enough for the frontend
                return parsed
                
            # If the LLM returned a flat JSON object like {"text": "..."}
            if isinstance(parsed, dict):
                content = parsed.get("text") or parsed.get("response") or parsed.get("content") or parsed.get("message")
                if content:
                    return {
                        "blocks": [
                            {
                                "id": "fallback-1",
                                "type": "text",
                                "data": {"content": str(content)},
                                "metadata": {"priority": "normal", "density": "comfortable"}
                            }
                        ]
                    }
        except json.JSONDecodeError:
            pass
            
        # Repair strategy: Fallback to a single text block
        return {
            "blocks": [
                {
                    "id": "fallback-1",
                    "type": "text",
                    "data": {"content": raw_output},
                    "metadata": {"priority": "normal", "density": "comfortable"}
                }
            ]
        }

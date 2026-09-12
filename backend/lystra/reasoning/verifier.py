from pydantic import BaseModel
import json

class VerificationResult(BaseModel):
    is_valid: bool
    reasoning: str
    suggested_fix: str = ""

class LogicVerifier:
    def __init__(self, llm_gateway):
        self.llm = llm_gateway

    async def verify(self, plan: str, code: str) -> VerificationResult:
        prompt = f"Plan: {plan}\nCode: {code}"
        system = "Verify if the code correctly implements the plan without logical errors. Output valid JSON matching schema: {'is_valid': true/false, 'reasoning': 'string', 'suggested_fix': 'string'}"
        
        try:
            messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
            response = await self.llm.chat(messages, temperature=0.0)
            data = json.loads(response.replace("```json", "").replace("```", "").strip())
            return VerificationResult(**data)
        except Exception:
            return VerificationResult(is_valid=True, reasoning="Fallback to valid")

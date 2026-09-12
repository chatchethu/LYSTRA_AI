with open('backend/lystra/memory/memory_classifier.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_logic = '''        try:
            # We assume llm.generate or similar exists. We'll use a mocked/generic call for now based on what's available
            if hasattr(self.llm, "generate_json"):
                response = await self.llm.generate_json(prompt)
                return response
            elif hasattr(self.llm, "generate"):
                response = await self.llm.generate(prompt)
                # Attempt to parse json
                start = response.find("{")
                end = response.rfind("}") + 1
                return json.loads(response[start:end])
            else:
                # Mock fallback
                return {
                    "type": "temporary_information",
                    "importance": 0.1,
                    "persistence": "none",
                    "reason": "Fallback generic response"
                }
        except Exception:'''

new_logic = '''        try:
            messages = [
                {"role": "system", "content": "You are a precise data classification system. Only output valid JSON matching the requested schema. No markdown wrapping."},
                {"role": "user", "content": prompt}
            ]
            response_text = await self.llm.chat(messages=messages, format="json")
            
            clean_text = response_text.replace("`json", "").replace("`", "").strip()
            start = clean_text.find("{")
            end = clean_text.rfind("}") + 1
            if start != -1 and end != 0:
                clean_text = clean_text[start:end]
            return json.loads(clean_text)
        except Exception:'''

content = content.replace(old_logic, new_logic)

with open('backend/lystra/memory/memory_classifier.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed memory_classifier LLM call")

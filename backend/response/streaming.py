import json

class JSONStreamParser:
    @staticmethod
    def extract_partial_blocks(partial_json: str) -> list:
        text = partial_json.strip()
        
        # Strip markdown scaffolding if present
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
            
        text = text.strip()
        
        if not text:
            return []
            
        try:
            parsed = json.loads(text)
            blocks = parsed.get("blocks")
            if isinstance(blocks, list):
                return blocks
            
            # If flat json
            if isinstance(parsed, dict):
                content = parsed.get("text") or parsed.get("response") or parsed.get("content") or parsed.get("message")
                if content:
                    return [{"type": "text", "data": {"content": str(content)}}]
            return []
        except json.JSONDecodeError:
            pass
            
        # The text is incomplete. It likely ends in the middle of a string or object.
        # Strategy: find the last occurrence of '{"type":' and try to cut the string before any broken parts.
        
        # A simpler, highly robust approach for streaming UI blocks:
        # We can extract all {"type": "...", ...} objects using a regex, even if the JSON is broken at the end.
        # Because we only care about rendering blocks that have 'type' and 'data'.
        
        # First, try to fix unclosed strings. Find the last quote.
        # This is a heuristic that works well for LLM streaming.
        
        # If it's an unclosed string, close it, close the object, close the array, close the root.
        fixes = [
            '"]}]}',
            '"}}]}',
            '"}',
            '"} ]}',
            '"] }',
            '} ]}',
            '}]}',
            ']}',
            '}'
        ]
        
        # Try to fix by appending quotes and brackets
        for fix in fixes:
            try:
                parsed = json.loads(text + fix)
                if isinstance(parsed, dict):
                    if "blocks" in parsed and isinstance(parsed["blocks"], list):
                        return parsed["blocks"]
                    content = parsed.get("text") or parsed.get("content")
                    if content:
                        return [{"type": "text", "data": {"content": str(content)}}]
            except json.JSONDecodeError:
                pass
                
        # If standard appending fails, maybe it's in the middle of a word without quotes?
        # Just close the string and brackets
        try:
            parsed = json.loads(text + '"}}]}')
            if isinstance(parsed, dict):
                if "blocks" in parsed and isinstance(parsed["blocks"], list):
                    return parsed["blocks"]
                content = parsed.get("text") or parsed.get("content")
                if content:
                    return [{"type": "text", "data": {"content": str(content)}}]
        except Exception:
            pass

        # Most robust fallback for partial blocks: 
        # Extract fully formed blocks using regex, ignoring the broken tail.
        # A block looks like {"type": "text", "data": {...}, ...}

        return []

import sys
import os
sys.path.append(os.path.abspath("."))
from backend.response.streaming import JSONStreamParser

partial = '{"blocks": [{"type": "text", "data": {"content": "Hello wo'
print(JSONStreamParser.extract_partial_blocks(partial))

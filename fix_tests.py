with open('backend/tests/test_lystra_memory.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Update mocks to return ClassificationSchema
new_mocks = '''from backend.lystra.memory.memory_classifier import ClassificationSchema
async def mock_classify_id(m): return ClassificationSchema(type="identity", persistence="long_term", importance=0.95, extracted_fact="Rahul")
async def mock_classify_irr(m): return ClassificationSchema(type="irrelevant_information", persistence="none")
async def mock_classify_com(m): return ClassificationSchema(type="communication_preference", persistence="long_term", importance=0.75)'''

content = re.sub(r'async def mock_classify_id.*?async def mock_classify_com\(m\): return \{.*?\}', new_mocks, content, flags=re.DOTALL)

with open('backend/tests/test_lystra_memory.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated memory mocks.")

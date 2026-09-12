with open('backend/tools/web/web_search.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

content = content.replace('model = model_router.get_model(TaskType.ROUTING)', 'model = getattr(model_router, "default_model", "llama3.2:latest")')

with open('backend/tools/web/web_search.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched WebSearchTool to support new ModelRouter")

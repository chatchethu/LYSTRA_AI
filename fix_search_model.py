with open('backend/tools/web/web_search.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_model_assign = '''        if llm and model_router and candidate_urls:
            model = getattr(model_router, "default_model", "llama3.2:latest")'''

new_model_assign = '''        if llm and model_router and candidate_urls:
            from backend.llm.model_router import TaskType
            if hasattr(model_router, "get_model"):
                model = model_router.get_model(TaskType.EXTRACTION)
            else:
                model = getattr(model_router, "default_model", "llama3.2:latest")'''

content = content.replace(old_model_assign, new_model_assign)

with open('backend/tools/web/web_search.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("web_search.py model router fixed")

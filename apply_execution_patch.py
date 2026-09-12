with open('backend/lystra/orchestration/execution_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Fix E: ExecutionManager freshness bypass
old_exec = '''                    search_result = await self.web_search_tool.execute(
                        user_id=user_id,
                        query=search_q,
                        queries=[],
                        llm=self.llm,
                        model_router=self.model_router
                    )'''

new_exec = '''                    search_result = await self.web_search_tool.execute(
                        user_id=user_id,
                        query=search_q,
                        queries=[],
                        llm=self.llm,
                        model_router=self.model_router,
                        freshness_required=True
                    )'''

content = content.replace(old_exec, new_exec)

with open('backend/lystra/orchestration/execution_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patched ExecutionManager")

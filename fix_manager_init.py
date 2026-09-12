with open('backend/lystra/orchestration/execution_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_init = '''        self.tool_router = ToolRouter(llm_gateway)
        self.web_search_tool = WebSearchTool()
        self.web_research_agent = WebResearchAgent(llm_gateway, model_router=self.model_router)'''

new_init = '''        self.tool_router = ToolRouter(llm_gateway)
        self.web_search_tool = WebSearchTool()
        self.web_research_agent = WebResearchAgent(llm_gateway, model_router=self.model_router)
        self.memory_manager = MemoryManager(llm_gateway)'''

content = content.replace(old_init, new_init)

with open('backend/lystra/orchestration/execution_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed memory_manager init")

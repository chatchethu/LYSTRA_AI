import re

with open('backend/lystra/orchestration/execution_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = r'''(elif tool_decision\.web_policy == WebSearchPolicy\.MANDATORY_WEB:\s+logger\.info\("executing_web_search", query=user_message\)\s+if stream_callback:\s+await stream_callback\("\*\(Searching the web\.\.\.\)\*\\n\\n"\)\s+search_result = await self\.web_search_tool\.execute\(\s+user_id=user_id,\s+query=user_message,\s+queries=\[\])'''

replacement = '''elif tool_decision.web_policy == WebSearchPolicy.MANDATORY_WEB:
                    search_q = getattr(tool_decision, "search_query", None) or user_message
                    logger.info("executing_web_search", original_query=user_message, optimized_query=search_q)
                    # if stream_callback:
                    #     await stream_callback(f"*(Searching the web for: {search_q}...)*\\n\\n")
                    
                    search_result = await self.web_search_tool.execute(
                        user_id=user_id,
                        query=search_q,
                        queries=[]'''

if re.search(pattern, content):
    content = re.sub(pattern, replacement, content)
    with open('backend/lystra/orchestration/execution_manager.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("ExecutionManager updated successfully.")
else:
    print("Could not find regex pattern in execution_manager.py")

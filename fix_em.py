with open('backend/lystra/orchestration/execution_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

old_block = '''                elif tool_decision.web_policy == WebSearchPolicy.MANDATORY_WEB:
                    logger.info("executing_web_search", query=user_message)
                    if stream_callback:
                        await stream_callback("*(Searching the web...)*\n\n")
                    
                    search_result = await self.web_search_tool.execute(
                        user_id=user_id,
                        query=user_message,
                        queries=[],
                        llm=self.llm,
                        model_router=self.model_router
                    )'''
new_block = '''                elif tool_decision.web_policy == WebSearchPolicy.MANDATORY_WEB:
                    search_q = getattr(tool_decision, "search_query", None) or user_message
                    logger.info("executing_web_search", original_query=user_message, optimized_query=search_q)
                    if stream_callback:
                        await stream_callback(f"*(Searching the web for: {search_q}...)*\n\n")
                    
                    search_result = await self.web_search_tool.execute(
                        user_id=user_id,
                        query=search_q,
                        queries=[],
                        llm=self.llm,
                        model_router=self.model_router
                    )'''

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('backend/lystra/orchestration/execution_manager.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("ExecutionManager updated successfully.")
else:
    print("Could not find block in execution_manager.py")

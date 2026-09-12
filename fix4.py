import re

with open("backend/agent/runtime.py", "r", encoding="utf-8") as f:
    text = f.read()

# I will replace the entire # 6. Execute based on mode up to # 7. Remember
pattern = re.compile(r'# 6\. Execute based on mode.*?# 7\. Remember', re.DOTALL)
replacement = """# 6. Execute based on mode
        if decision.action_type in ["direct_response", "clarification"]:
            if stream_callback:
                await stream_callback("agent.thinking", {"status": "Generating response..."})
            task_type = TaskType.CODE if current_intent == "coding" else (TaskType.RESEARCH if current_intent == "research" else (TaskType.DOCUMENT if request.file_id else TaskType.CHAT))
            response_obj = await self.llm.chat(messages=context, model=model_def.id if model_def else "llama3.2:latest")
            from backend.agent.response_manager import ResponseManager
            canonical = ResponseManager.parse_blocks(response_obj)
            import json
            final_response_text = json.dumps([b.model_dump() for b in canonical.blocks])
            
        elif decision.action_type == "single_tool":
            if stream_callback:
                await stream_callback("agent.thinking", {"status": f"Executing {decision.selected_tools[0]}..."})
            tool_name = decision.selected_tools[0]
            try:
                tool = registry.get_tool(tool_name)
                if not tool:
                    raise Exception(f"Tool {tool_name} not found")
                res = await tool.execute(user_id=request.user_id, query=message)
                tool_results.append({"tool": tool_name, "result": res})
                
                # Build context again with tool result and get final response
                context = self.context_manager.build_context(
                    system_policy=prompt_registry.get_prompt("system_policy_main")["content"],
                    agent_policy="Incorporate tool results to provide a comprehensive answer.",
                    user_profile=str(prefs),
                    relevant_ltm=relevant_ltm,
                    active_task_state=active_task_state,
                    conversation_summary="",
                    recent_messages=history,
                    current_tool_results=tool_results,
                    current_message=message,
                    topic_changed=False,
                    task_changed=False
                )
                task_type = TaskType.CODE if current_intent == "coding" else (TaskType.RESEARCH if current_intent == "research" else (TaskType.DOCUMENT if request.file_id else TaskType.CHAT))
                response_obj = await self.llm.chat(messages=context, model=model_def.id if model_def else "llama3.2:latest")
                from backend.agent.response_manager import ResponseManager
                canonical = ResponseManager.parse_blocks(response_obj)
                import json
                final_response_text = json.dumps([b.model_dump() for b in canonical.blocks])
            except Exception as e:
                final_response_text = f"Tool execution failed: {str(e)}"
                
        elif decision.action_type == "multi_step_task":
            if stream_callback:
                await stream_callback("agent.thinking", {"status": "Planning multi-step execution..."})
            available_tools = list(registry.tools.keys())
            plan = await self.planner.create_plan(message, context, available_tools)
            
            task = await self.task_manager.create_task(
                user_id=request.user_id,
                title="Auto-generated Task",
                goal=message
            )
            state.active_task_id = str(task.id)
            await self.task_manager.save_plan(task.id, plan)
            
            plan = await self._execute_plan_loop(plan, task.id, {"user_id": user_id, "conversation_id": conversation_id}, stream_callback=stream_callback)
            
            final_response_text = f"I have completed the multi-step task. {len([s for s in plan.steps if s.status == 'completed'])} steps were completed."

        # 7. Remember"""
text = pattern.sub(replacement, text)

with open("backend/agent/runtime.py", "w", encoding="utf-8") as f:
    f.write(text)

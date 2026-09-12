with open("backend/agent/runtime.py", "r") as f:
    content = f.read()

target = """        context = self.context_manager.build_context(
            system_policy=prompt_registry.get_prompt("system_policy_main")["content"],
            agent_policy="Provide comprehensive, well-structured answers.",
            user_profile=str(prefs),
            relevant_ltm=relevant_ltm, 
            active_task_state=active_task_state,
            conversation_summary="",
            recent_messages=history,
            current_message=message + ("\\n\\n" + doc_context if doc_context else ""),
            topic_changed=topic_changed,
            task_changed=task_changed
        )"""

replacement = """        context = self.context_manager.build_context(
            system_policy=prompt_registry.get_prompt("system_policy_main")["content"],
            agent_policy="Provide comprehensive, well-structured answers.",
            user_profile=str(prefs),
            relevant_ltm=relevant_ltm, 
            active_task_state=active_task_state,
            conversation_summary="",
            recent_messages=history,
            current_tool_results=[],
            current_message=message + ("\\n\\n" + doc_context if doc_context else ""),
            topic_changed=topic_changed,
            task_changed=task_changed
        )"""

content = content.replace(target, replacement)

with open("backend/agent/runtime.py", "w") as f:
    f.write(content)
print("Replaced properly!")

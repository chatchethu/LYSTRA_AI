import sys

with open('backend/agent/runtime.py', 'r') as f:
    content = f.read()

# Let's see what was broken. It removed `generate_draft` in lines 331-355
# I will use a script to find `if decision.action_type in ["direct_response", "clarification"]:` and fix it.

target = '''        if decision.action_type in ["direct_response", "clarification"]:
            if stream_callback:
                await stream_callback("agent.thinking", {"status": "Generating response..."})
            )
            
            # CI-22: Score user satisfaction asynchronously in background'''

replacement = '''        if decision.action_type in ["direct_response", "clarification"]:
            if stream_callback:
                await stream_callback("agent.thinking", {"status": "Generating response..."})
            task_type = TaskType.CODE if current_intent == "coding" else (TaskType.RESEARCH if current_intent == "research" else (TaskType.DOCUMENT if request.file_id else TaskType.CHAT))
            
            final_response_text = ""
            if stream_callback:
                async for chunk in self.llm.stream(messages=context, model=chat_model_id):
                    final_response_text += chunk
                    await stream_callback("message.delta", {"content": chunk})
            else:
                response_obj = await self.llm.chat(messages=context, model=chat_model_id)
                from backend.agent.response_manager import ResponseManager
                canonical = ResponseManager.parse_blocks(response_obj)
                import json
                final_response_text = json.dumps([b.model_dump() for b in canonical.blocks])
            
            # CI-22: Score user satisfaction asynchronously in background'''

content = content.replace(target, replacement)

# We also need to fix the other occurrence around line 444 which I tried to replace earlier.
target2 = '''          if decision.action_type == "direct_response":
              
              # ── CI-24: Run inside Response Revision Loop ──
              async def generate_draft(prompt_updates: str) -> str:
                  # If there are revision prompt updates, we append them to the final context message
                  mutated_context = context.copy()
                  if prompt_updates:
                      # The prompt_updates is actually the base_prompt in run_loop.
                      # run_loop passes the entire current base_prompt back to generate_func.
                      # Because `base_prompt` is initialized to "", prompt_updates is just the accumulated feedback.
                      if prompt_updates:
                          mutated_context[-1] = {"role": "user", "content": mutated_context[-1]["content"] + prompt_updates}
                  response_obj = await self.llm.chat(messages=mutated_context, model=chat_model_id)
                  from backend.agent.response_manager import ResponseManager
                  canonical = ResponseManager.parse_blocks(response_obj)
                  import json
                  return json.dumps([b.model_dump() for b in canonical.blocks])

              final_response_text = await self.revision_loop.run_loop(
                  generate_draft, 
                  "", 
                  history, 
                  need=ci_result.detected_need if ci_result else None, 
                  mode=ci_result.mode if ci_result else None
              )
              
              # CI-22: Score user satisfaction asynchronously in background'''

replacement2 = '''          if decision.action_type == "direct_response":
              final_response_text = ""
              if stream_callback:
                  async for chunk in self.llm.stream(messages=context, model=chat_model_id):
                      final_response_text += chunk
                      await stream_callback("message.delta", {"content": chunk})
              else:
                  response_obj = await self.llm.chat(messages=context, model=chat_model_id)
                  from backend.agent.response_manager import ResponseManager
                  canonical = ResponseManager.parse_blocks(response_obj)
                  import json
                  final_response_text = json.dumps([b.model_dump() for b in canonical.blocks])
              
              # CI-22: Score user satisfaction asynchronously in background'''

content = content.replace(target2, replacement2)

with open('backend/agent/runtime.py', 'w') as f:
    f.write(content)

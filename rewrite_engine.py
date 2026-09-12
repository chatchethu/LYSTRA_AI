import re

with open("backend/orchestration/conversation_engine.py", "r", encoding="utf-8") as f:
    content = f.read()

# We want to replace everything from `async def process_turn` to the end of `process_turn`
# Since it's a huge method, let's just find `def process_turn` and find the end by looking for `return response_text, state, summary, task, prefs, tool_results_raw, revision_triggered, metadata`

start_idx = content.find("    async def process_turn(")
end_idx = content.find("return response_text, agent_state.session_context, summary, task, prefs, tool_dicts, False, metadata", start_idx)

if start_idx == -1 or end_idx == -1:
    print(f"Could not find bounds of process_turn: start={start_idx} end={end_idx}")
else:
    # We include the return statement in the slice
    end_idx = content.find("\n", end_idx) + 1
    
    new_process_turn = """    async def process_turn(
        self,
        message: str,
        conversation_id: str,
        history: List[Dict[str, str]],
        state: ConversationState,
        summary: Optional[ConversationSummary],
        task: Optional[ActiveTask],
        prefs: UserPreferences,
        memory: MemoryService,
        user_id: str,
        stream_callback=None,
        file_context=None,   # Multimodal V1: Optional FileContext
    ) -> Tuple[str, ConversationState, Optional[ConversationSummary], Optional[ActiveTask], UserPreferences, List[dict], bool, Dict[str, Any]]:
        \"\"\"
        Phase 33 & 34: 25-step chronological pipeline.
        Returns: (response_text, new_state, new_summary, new_task, new_prefs, tool_results, revision_triggered, metadata)
        \"\"\"
        # 1. Message Understanding (Phases 1-10)
        from backend.intelligence.message_understanding import MessageUnderstander
        understander = MessageUnderstander(self.llm)
        understanding = await understander.analyze(message, history, state)
        
        # 2. Update Conversation State & Detect Transitions (Phases 11-12)
        from backend.conversation.transition_detector import TransitionDetector
        is_transition = TransitionDetector.detect_transition(understanding, state)
        
        state.conversation_stage = understanding.conversation_stage
        state.active_target = understanding.target
        state.emotion = understanding.emotion
        state.emotion_intensity = understanding.emotion_intensity
        state.active_topic = understanding.topic
        
        # 3. Tool & Web Routing (Phases 20-27)
        from backend.tools.tool_router import ToolRouter, WebSearchPolicy
        router = ToolRouter(self.llm)
        tool_decision = await router.route(message)
        
        tool_results_raw = []
        tool_context = ""
        
        if tool_decision.web_policy == WebSearchPolicy.MANDATORY_WEB:
            if stream_callback:
                await stream_callback("searchState", {"status": "searching", "query": message})
            from backend.tools.registry import registry
            search_res_dict = await registry.execute_tool("web_search", {"query": message, "max_results": 3})
            
            if isinstance(search_res_dict, dict) and "formatted" in search_res_dict:
                tool_context += f"WEB SEARCH EVIDENCE:\\n{search_res_dict['formatted']}\\n\\n"
                if stream_callback:
                    await stream_callback("searchState", {"status": "complete", "sources": search_res_dict.get("sources", [])})
            else:
                if stream_callback:
                    await stream_callback("searchState", {"status": "error"})
                    
        # Load Personality Profile
        if conversation_id not in self.profiles:
            self.profiles[conversation_id] = PersonalityProfile()
        profile = self.profiles[conversation_id]
        
        # 4. Response Strategy (Phases 15-19)
        from backend.personality.strategy import StrategyPlanner
        strategy_planner = StrategyPlanner(self.llm, self.model_router)
        strategy = await strategy_planner.plan_strategy(understanding, state)
        
        # Adjust Personality (Defensiveness=0 for complaints)
        if understanding.target == "NOVA" and understanding.speech_act in ("complaint", "blaming"):
            profile.warmth = min(1.0, profile.warmth + 0.1)
            # Defensiveness = 0 is a concept enforced in the prompt
            
        # 5. Build Context & Generate (Phases 17-18)
        from backend.personality.prompt_builder import build_dynamic_system_prompt
        # For simplicity in integration, we fake a StrategyResult object for the prompt builder
        from pydantic import BaseModel
        class FakeStrategy(BaseModel):
            strategy: List[str]
            mode: str
        legacy_strategy = FakeStrategy(strategy=[strategy.primary_action, strategy.secondary_action], mode=strategy.tone)
        
        prompt = build_dynamic_system_prompt(
            state=state,
            profile=profile,
            strategy=legacy_strategy,
            tool_evidence=tool_context,
            memory_context=""
        )
        
        messages = [{"role": "system", "content": prompt}]
        for msg in history[-8:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": message})
        
        if stream_callback:
            await stream_callback("state", "generating")
            
        model = self.model_router.get_model(TaskType.CHAT)
        kwargs = self.model_router.get_provider_kwargs(TaskType.CHAT)
        
        try:
            if stream_callback:
                response_text = ""
                async for chunk in self.llm.stream(messages, model=model, **kwargs):
                    if hasattr(chunk, "content"):
                        response_text += chunk.content
                    elif isinstance(chunk, dict) and "content" in chunk:
                        response_text += chunk["content"]
                    await stream_callback("chunk", chunk)
            else:
                response_text = await self.llm.chat(messages, model=model, **kwargs)
        except Exception as e:
            response_text = f"An error occurred: {str(e)}"
            
        # 6. Quality Validation & Repair (Phases 28-30)
        from backend.validation.quality import QualityEvaluator
        evaluator = QualityEvaluator(self.llm)
        eval_score = await evaluator.evaluate(response_text, message, history, [strategy.primary_action])
        
        revision_triggered = False
        if eval_score.needs_repair:
            revision_triggered = True
            if stream_callback:
                await stream_callback("status", {"text": "Improving response naturalness...", "type": "repair"})
                
            from backend.generation.repair import repair_response
            response_text = await repair_response(
                self.llm, response_text, message, prompt, [strategy.primary_action]
            )
            
            if stream_callback:
                await stream_callback("revision", {"text": response_text})

        # Save thread
        if hasattr(self, 'threads') and conversation_id in self.threads:
            self.threads[conversation_id].add_message("user", message)
            self.threads[conversation_id].add_message("assistant", response_text)

        metadata = {
            "intent": understanding.intent,
            "target": understanding.target,
            "web_policy": tool_decision.web_policy.value,
            "strategy": strategy.primary_action
        }

        return response_text, state, summary, task, prefs, tool_results_raw, revision_triggered, metadata
"""

    new_content = content[:start_idx] + new_process_turn + content[end_idx:]
    with open("backend/orchestration/conversation_engine.py", "w", encoding="utf-8") as out:
        out.write(new_content)
    print("Successfully patched process_turn!")

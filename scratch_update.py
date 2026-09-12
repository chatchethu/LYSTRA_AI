import re
with open('backend/intelligence/analyzer.py', 'r') as f:
    content = f.read()

replacement = \"\"\"        # --- Topic, Intent, Task separation (Phase 8 & 9) ---
        # A topic changes if the new topic is different from the current topic and not 'general'.
        
        topic_changed = False
        if state.current_topic and state.current_topic != 'general' and topic != 'general' and topic != state.current_topic:
            topic_changed = True
            
        intent_changed = False
        if state.current_intent and state.current_intent != intent:
            intent_changed = True
            
        # A task changes if the intent changes drastically (e.g. travel -> coding) or if topic changes drastically.
        # But if the user says 'continue the Goa trip', the intent might be 'travel' again, reverting to the old task.
        task_changed = topic_changed or intent_changed
        
        previous_topic = state.current_topic if topic_changed else state.previous_topic
        current_topic = topic if topic != 'general' else state.current_topic
        
        previous_intent = state.current_intent if intent_changed else state.previous_intent
        current_intent = intent
        
        previous_task = state.current_task if task_changed else state.previous_task
        current_task = goal if task_changed else state.current_task

        # --- Clarification needed? ---
        needs_clarification = (ambiguity > 0.6 and risk >= RiskLevel.HIGH) or (
            ambiguity > 0.8
        )
        # Never ask for clarification for dangerous destructive ops — always confirm
        if risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            needs_clarification = True

        # --- Update rolling state ---
        new_state = ConversationState(
            previous_topic=previous_topic,
            current_topic=current_topic,
            topic_changed=topic_changed,
            
            previous_intent=previous_intent,
            current_intent=current_intent,
            intent_changed=intent_changed,
            
            previous_task=previous_task,
            current_task=current_task,
            task_changed=task_changed,
            
            active_task_id=state.active_task_id, # to be managed by task manager
            turn_count=state.turn_count + 1,
            
            active_goal=goal,
            goal_status=state.goal_status,
        )

        contract = ConversationContract(
            intent=intent,
            topic=current_topic or 'general',
            user_goal=current_task or goal,\"\"\"

content = re.sub(
    r'# --- Topic switch detection ---.*?user_goal=goal,',
    replacement,
    content,
    flags=re.DOTALL
)

with open('backend/intelligence/analyzer.py', 'w') as f:
    f.write(content)

import sys

with open('backend/workers/tasks.py', 'r') as f:
    lines = f.readlines()

new_lines = []
in_try = False

for line in lines:
    if 'execution_manager = ExecutionManager(bg_llm)' in line:
        new_lines.append('        try:\n')
        new_lines.append('            bg_llm = None; chat_message = ""; history = []; bg_db = db; cid = None; uid = None; state = None; bg_conv = None; meta = {}; idem_key = None\n')
        new_lines.append('            execution_manager = ExecutionManager(bg_llm)\n')
        in_try = True
    elif line.startswith('    except Exception as e:'):
        new_lines.append('        except Exception as e:\n')
    elif line.startswith('        import traceback') and in_try:
        new_lines.append('            import traceback\n')
    elif line.startswith('        traceback.print_exc()') and in_try:
        new_lines.append('            traceback.print_exc()\n')
    elif line.startswith('        await outbox_publish("run.failed"') and in_try:
        new_lines.append('            pass\n')
    elif line.startswith('    finally:'):
        new_lines.append('        finally:\n')
    elif line.startswith('        await outbox_publish("message.completed"') and in_try:
        new_lines.append('            pass\n')
    elif line.startswith('        await outbox_publish("run.completed"') and in_try:
        new_lines.append('            pass\n')
    elif line.startswith('        if idem_key:') and in_try:
        new_lines.append('            pass\n')
    elif line.startswith('            async with AsyncSessionLocal() as bg_db:') and in_try:
        pass
    elif line.startswith('                await save_idempotency_result') and in_try:
        pass
    else:
        new_lines.append(line)

with open('backend/workers/tasks.py', 'w') as f:
    f.writelines(new_lines)

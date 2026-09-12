with open("backend/agent/runtime.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip_next = False
for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue

    # Insert model_def definition before step 6
    if "6. Execute based on mode" in line:
        new_lines.append("        try:\n")
        new_lines.append("            model_def = self.model_router.registry.get_model(self.model_router.get_model(TaskType.CHAT))\n")
        new_lines.append("        except:\n")
        new_lines.append("            model_def = None\n")
        new_lines.append(line)
        continue
    
    # Check for duplicated response_obj
    if "response_obj = await self.llm.chat(" in line:
        # if the next line is exactly the same, skip it
        if i + 1 < len(lines) and lines[i+1].strip() == line.strip():
            skip_next = True

    new_lines.append(line)

with open("backend/agent/runtime.py", "w") as f:
    f.writelines(new_lines)
print("Fixed model_def and duplicate line.")

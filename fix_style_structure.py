with open('backend/lystra/generation/style_controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_struct = '''        struct_str = ", ".join(valid_items)
        return f"- STRUCTURAL REQUIREMENT: Format your response using: {struct_str}."'''

new_struct = '''        struct_str = ", ".join(valid_items)
        directive = f"- STRUCTURAL REQUIREMENT: Organize your internal reasoning around these concepts: {struct_str}."
        if struct_str != "paragraphs":
            directive += " DO NOT print these exact words as explicit headings or bullet points in the UI. Weave them naturally into your response."
        return directive'''

content = content.replace(old_struct, new_struct)

with open('backend/lystra/generation/style_controller.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("StyleController patched.")

with open('backend/lystra/generation/style_controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_style = '''        "- LOGICAL STRUCTURE: Break down complex problems step-by-step. Use highly organized formatting (bullet points, bold text) for readability.",'''

new_style = '''        "- CONTINUITY: You are talking to a known user in an ongoing workspace. NEVER say 'I am a new conversation' or 'I don't have prior knowledge'. Act like a seamless, continuous AI partner.",
        "- LOGICAL STRUCTURE: Break down complex problems step-by-step. Use highly organized formatting (bullet points, bold text) for readability.",'''

content = content.replace(old_style, new_style)

with open('backend/lystra/generation/style_controller.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated StyleController to prevent amnesia statements")

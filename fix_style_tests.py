with open('backend/tests/test_style_controller.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_1 = '''    assert "- STRUCTURAL REQUIREMENT: Format your response using: paragraphs." in prompt'''
new_1 = '''    assert "- STRUCTURAL REQUIREMENT: Organize your internal reasoning around these concepts: paragraphs." in prompt'''

old_2 = '''    assert "- STRUCTURAL REQUIREMENT: Format your response using: paragraphs, tables DROP TABLE users" in prompt'''
new_2 = '''    assert "- STRUCTURAL REQUIREMENT: Organize your internal reasoning around these concepts: paragraphs, tables DROP TABLE users" in prompt'''

content = content.replace(old_1, new_1).replace(old_2, new_2)

with open('backend/tests/test_style_controller.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Tests patched.")

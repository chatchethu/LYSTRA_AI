import os
import re

directories = ['frontend', 'backend']
extensions = ('.ts', '.tsx', '.py', '.md')

replacements = [
    (r'\bNOVA\b', 'LYSTRA'),
    (r'\bNova\b', 'Lystra'),
    (r'\bnova\b', 'lystra')
]

for d in directories:
    for root, dirs, files in os.walk(d):
        if 'node_modules' in root or '.next' in root or '__pycache__' in root:
            continue
        for f in files:
            if f.endswith(extensions):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        content = file.read()
                    
                    new_content = content
                    for pattern, repl in replacements:
                        new_content = re.sub(pattern, repl, new_content)
                        
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8') as file:
                            file.write(new_content)
                        print(f"Updated {filepath}")
                except Exception as e:
                    pass
print("Done!")

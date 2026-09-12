with open('backend/lystra/orchestration/execution_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_string = '''                    #     await stream_callback(f"*(Searching the web for: {search_q}...)*

")'''

good_string = '''                    #     await stream_callback(f"*(Searching the web for: {search_q}...)*\\n\\n")'''

content = content.replace(bad_string, good_string)

with open('backend/lystra/orchestration/execution_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed syntax")

with open('backend/lystra/orchestration/execution_manager.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_stream = '''                    # if stream_callback:
                    #     await stream_callback(f"*(Searching the web for: {search_q}...)*\\n\\n")'''

new_stream = '''                    if stream_callback:
                        await stream_callback(f"*(Searching the web for: {search_q}...)*\\n\\n")'''

content = content.replace(old_stream, new_stream)

with open('backend/lystra/orchestration/execution_manager.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Uncommented stream_callback for web search")

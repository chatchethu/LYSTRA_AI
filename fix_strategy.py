with open('backend/lystra/generation/response_strategy.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

old_overrides = '''        # Emotional Overrides
        if emotion == "frustrated":
            tone = "empathetic"
            emoji_use = False # Prioritize clarity and empathy
        elif emotion == "celebratory":
            tone = "celebratory"
            emoji_purpose = "celebration"
            emoji_intensity = "high" if state_affinity == "high" else "medium"
            
        # Intent Overrides
        if intent == "problem_solving":
            depth = "comprehensive"
            tone = "focused" if tone == "neutral" else tone
            structure = ["problem_summary", "cause", "fix_steps", "verification"]
            emoji_use = False
        elif intent == "conversation":'''

new_overrides = '''        # Intent Overrides
        if intent == "problem_solving":
            depth = "comprehensive"
            tone = "focused" if tone == "neutral" else tone
            structure = ["problem_summary", "cause", "fix_steps", "verification"]
            emoji_use = False
        elif intent == "conversation":
            depth = "concise"
            tone = "warm" if tone == "neutral" else tone
            structure = ["paragraphs"]

        # Emotional Overrides (Evaluated after intent so emotion trumps task structure)
        if emotion in ["frustrated", "sad"]:
            tone = "empathetic"
            depth = "concise" # Keep emotional responses human and brief, not encyclopedic
            structure = ["paragraphs"] # Strip mechanical bullet points for emotional topics
            emoji_use = False # Prioritize clarity and empathy
        elif emotion == "celebratory":
            tone = "celebratory"
            emoji_purpose = "celebration"
            emoji_intensity = "high" if state_affinity == "high" else "medium"
        elif emotion == "confused":
            tone = "warm"
            depth = "standard"
            structure = ["paragraphs"]
'''

content = content.replace(old_overrides, new_overrides)

with open('backend/lystra/generation/response_strategy.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("StrategyEngine patched.")

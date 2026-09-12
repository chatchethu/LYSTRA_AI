with open('backend/lystra/understanding/schemas.py', 'r', encoding='utf-8') as f:
    content = f.read()

import re

# Add pre validator to HierarchicalIntent
old_intent = '''class HierarchicalIntent(BaseModel):
    primary: PrimaryIntent = Field(description="The top-level intent category")'''

new_intent = '''class HierarchicalIntent(BaseModel):
    primary: PrimaryIntent = Field(description="The top-level intent category")

    @field_validator('primary', mode='before')
    def validate_primary(cls, v):
        try:
            return PrimaryIntent(v)
        except ValueError:
            return PrimaryIntent.CONVERSATION'''

content = content.replace(old_intent, new_intent)

with open('backend/lystra/understanding/schemas.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Added coercion validator for PrimaryIntent")

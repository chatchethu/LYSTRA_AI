with open('backend/tools/executor.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "from backend.db.models.permission import ApprovalRequestModel",
    "from backend.db.models.approval import ApprovalRequest as ApprovalRequestModel"
)

with open('backend/tools/executor.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed executor imports")

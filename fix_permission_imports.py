with open('backend/tools/permissions.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "from backend.db.models.permission import ToolPermission, ApprovalRequestModel, ExecutionLogModel",
    "from backend.db.models.permission import ToolPermission, ExecutionLogModel\nfrom backend.db.models.approval import ApprovalRequest as ApprovalRequestModel"
)

with open('backend/tools/permissions.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Fixed imports")

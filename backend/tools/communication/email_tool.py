from typing import List
from backend.tools import BaseTool, ToolPermissionLevel, ToolRiskLevel, ToolResult

class ReadEmailTool(BaseTool):
    name = "read_email"
    description = "Read emails from configured email account"
    permission_level = ToolPermissionLevel.COMMUNICATION
    risk_level = ToolRiskLevel.MEDIUM
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "mailbox": {"type": "string", "default": "INBOX"},
                "limit": {"type": "integer", "default": 10},
                "unread_only": {"type": "boolean", "default": True}
            }
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, mailbox: str = "INBOX", limit: int = 10, unread_only: bool = True) -> ToolResult:
        # Mock implementation. Real one would use imaplib or an API (e.g., MS Graph, Gmail API)
        return ToolResult(
            success=True,
            data={"emails": [
                {"subject": "Mock Email 1", "from": "sender@example.com", "snippet": "Hello world"},
                {"subject": "Mock Email 2", "from": "updates@example.com", "snippet": "System update"}
            ]}
        )

class SendEmailTool(BaseTool):
    name = "send_email"
    description = "Send an email (requires approval)"
    permission_level = ToolPermissionLevel.COMMUNICATION
    risk_level = ToolRiskLevel.HIGH
    requires_approval = True
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "to": {"type": "array", "items": {"type": "string"}},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "cc": {"type": "array", "items": {"type": "string"}, "default": []}
            },
            "required": ["to", "subject", "body"]
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, to: List[str], subject: str, body: str, cc: List[str] = []) -> ToolResult:
        # Mock implementation. Real one would use smtplib or API
        return ToolResult(
            success=True,
            data={"status": "sent", "to": to, "subject": subject}
        )

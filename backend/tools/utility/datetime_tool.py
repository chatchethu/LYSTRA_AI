from datetime import datetime
import zoneinfo
from backend.tools import BaseTool, ToolPermissionLevel, ToolRiskLevel, ToolResult

class DateTimeTool(BaseTool):
    name = "get_datetime"
    description = "Get current date, time, and timezone information"
    permission_level = ToolPermissionLevel.READ
    risk_level = ToolRiskLevel.LOW
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "timezone": {"type": "string", "default": "UTC"},
                "format": {"type": "string", "default": "iso"}
            }
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, timezone: str = "UTC", format: str = "iso") -> ToolResult:
        try:
            tz = zoneinfo.ZoneInfo(timezone)
            now = datetime.now(tz)
            
            if format == "iso":
                formatted = now.isoformat()
            else:
                formatted = now.strftime(format)
                
            return ToolResult(success=True, data={
                "datetime": formatted,
                "timezone": timezone,
                "is_dst": bool(now.dst())
            })
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

class TimerTool(BaseTool):
    name = "set_reminder"
    description = "Set a reminder or timer"
    permission_level = ToolPermissionLevel.WRITE
    risk_level = ToolRiskLevel.LOW
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "delay_minutes": {"type": "integer"},
                "recurring": {"type": "boolean", "default": False}
            },
            "required": ["message", "delay_minutes"]
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, message: str, delay_minutes: int, recurring: bool = False) -> ToolResult:
        # In a real app, this would schedule a background task via Celery or apscheduler
        return ToolResult(
            success=True, 
            data={"status": f"Reminder set for {delay_minutes} minutes from now", "message": message}
        )

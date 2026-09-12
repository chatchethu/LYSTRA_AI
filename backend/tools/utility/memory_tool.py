from backend.tools import BaseTool, ToolPermissionLevel, ToolRiskLevel, ToolResult

class RememberTool(BaseTool):
    name = "remember"
    description = "Store important information in long-term memory"
    permission_level = ToolPermissionLevel.WRITE
    risk_level = ToolRiskLevel.LOW
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "category": {"type": "string"},
                "importance": {"type": "number", "default": 0.5}
            },
            "required": ["content", "category"]
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, content: str, category: str, importance: float = 0.5) -> ToolResult:
        # Mock implementation. Real one would insert into vector DB or relational DB
        return ToolResult(
            success=True,
            data={"message": f"Successfully remembered '{content[:20]}...' in category {category}"}
        )

class RecallTool(BaseTool):
    name = "recall"
    description = "Search long-term memory for relevant information"
    permission_level = ToolPermissionLevel.READ
    risk_level = ToolRiskLevel.LOW
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, query: str, limit: int = 5) -> ToolResult:
        # Mock implementation. Real one would query vector DB
        return ToolResult(
            success=True,
            data={"results": [
                {"content": "Mock memory result related to query", "category": "general", "importance": 0.8}
            ]}
        )

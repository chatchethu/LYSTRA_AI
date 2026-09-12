from backend.tools import BaseTool, ToolPermissionLevel, ToolRiskLevel, ToolResult

class CodeRunnerTool(BaseTool):
    name = "run_code"
    description = "Execute Python code in a sandboxed environment"
    permission_level = ToolPermissionLevel.EXECUTE
    risk_level = ToolRiskLevel.HIGH
    requires_approval = False  # Allowing since sandboxed
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
                "language": {"type": "string", "default": "python"},
                "timeout": {"type": "integer", "default": 30}
            },
            "required": ["code"]
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, code: str, language: str = "python", timeout: int = 30) -> ToolResult:
        if language != "python":
            return ToolResult(success=False, data=None, error="Only Python is currently supported")
            
        try:
            from backend.sandbox.docker_executor import DockerExecutor
            result = await DockerExecutor.execute(code, timeout=timeout)
            
            if "error" in result and not result["success"]:
                return ToolResult(success=False, data=None, error=result["error"])
                
            return ToolResult(
                success=result["success"],
                data={
                    "stdout": result["stdout"],
                    "stderr": result["stderr"],
                    "exit_code": result["exit_code"]
                }
            )
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

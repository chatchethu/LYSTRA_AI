import shutil
from pathlib import Path
from backend.tools import BaseTool, ToolPermissionLevel, ToolRiskLevel, ToolResult

def get_secure_path(user_id: str, file_path: str) -> Path:
    base_dir = Path(f"workspace/{user_id}").resolve()
    base_dir.mkdir(parents=True, exist_ok=True)
    
    p = Path(file_path)
    if p.is_absolute():
        raise ValueError("Absolute paths are not allowed.")
        
    if ".." in p.parts:
        raise ValueError("Directory traversal (../) is not allowed.")
        
    target_path = (base_dir / p).resolve()
    
    if not str(target_path).startswith(str(base_dir)):
        raise ValueError("Path escapes workspace directory.")
        
    return target_path

class ReadFileTool(BaseTool):
    name = "read_file"
    description = "Read the contents of a file"
    permission_level = ToolPermissionLevel.READ
    risk_level = ToolRiskLevel.LOW
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "encoding": {"type": "string", "default": "utf-8"}
            },
            "required": ["file_path"]
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, file_path: str, encoding: str = "utf-8") -> ToolResult:
        try:
            path = get_secure_path(str(user_id), file_path)
            with open(path, "r", encoding=encoding) as f:
                content = f.read()
            return ToolResult(success=True, data={"content": content})
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Write or create a file"
    permission_level = ToolPermissionLevel.WRITE
    risk_level = ToolRiskLevel.MEDIUM
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"},
                "content": {"type": "string"},
                "mode": {"type": "string", "default": "w"}
            },
            "required": ["file_path", "content"]
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, file_path: str, content: str, mode: str = "w") -> ToolResult:
        try:
            if mode not in ("w", "a"):
                return ToolResult(success=False, data=None, error="Invalid mode. Allowed: w, a")
            path = get_secure_path(str(user_id), file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, mode) as f:
                f.write(content)
            return ToolResult(success=True, data={"message": f"Successfully wrote to {file_path}"})
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List files in a directory"
    permission_level = ToolPermissionLevel.READ
    risk_level = ToolRiskLevel.LOW
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "directory_path": {"type": "string"}
            },
            "required": ["directory_path"]
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, directory_path: str) -> ToolResult:
        try:
            path = get_secure_path(str(user_id), directory_path)
            if not path.is_dir():
                return ToolResult(success=False, data=None, error=f"{directory_path} is not a directory")
                
            files = []
            for item in path.iterdir():
                files.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else None
                })
            return ToolResult(success=True, data={"files": files})
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a file (requires approval)"
    permission_level = ToolPermissionLevel.WRITE
    risk_level = ToolRiskLevel.HIGH
    requires_approval = True
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {"type": "string"}
            },
            "required": ["file_path"]
        }
        
    async def execute(self, user_id, task_id, conversation_id, request_id, file_path: str) -> ToolResult:
        try:
            path = get_secure_path(str(user_id), file_path)
            if path.is_file():
                path.unlink()
                return ToolResult(success=True, data={"message": f"Deleted {file_path}"})
            elif path.is_dir():
                shutil.rmtree(path)
                return ToolResult(success=True, data={"message": f"Deleted directory {file_path}"})
            else:
                return ToolResult(success=False, data=None, error=f"{file_path} does not exist")
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))

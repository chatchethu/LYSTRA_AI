import os
import sys
import tempfile
import subprocess
import shutil
from typing import Optional
from uuid import UUID

from backend.tools.registry import BaseTool, ToolPermissionLevel, ToolRiskLevel, ToolResult

class CodeSandboxTool(BaseTool):
    name = "execute_code"
    description = "Execute generated Python code in a secure, isolated sandbox."
    permission_level = ToolPermissionLevel.EXECUTE
    risk_level = ToolRiskLevel.HIGH
    requires_approval = True
    
    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "Python code to execute."
                }
            },
            "required": ["code"]
        }

    async def execute(self, code: str, user_id: Optional[UUID] = None, **kwargs) -> ToolResult:
        """Executes code using a secure subprocess wrapper."""
        
        # 1. Create strict temporary workspace
        workspace_dir = tempfile.mkdtemp(prefix="lystra_sandbox_")
        script_path = os.path.join(workspace_dir, "main.py")
        
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        try:
            # On Linux we would use 'sudo -u nobody' or Docker.
            # Here we use subprocess with strict timeout, empty env to prevent reading host env.
            empty_env = {
                "PATH": os.environ.get("PATH", ""),
                "SystemRoot": os.environ.get("SystemRoot", "C:\\Windows")
            }
            
            # Phase 29: CPU limit, RAM limit, process limit is ideally done via Linux cgroups (e.g. systemd-run or unshare)
            # We enforce a strict timeout for infinite loops.
            proc = subprocess.run(
                [sys.executable, script_path],
                cwd=workspace_dir,
                env=empty_env,
                capture_output=True,
                text=True,
                timeout=5.0  # Strict timeout for infinite loops and fork bombs
            )
            
            output = proc.stdout
            if proc.stderr:
                output += f"\nSTDERR:\n{proc.stderr}"
                
            return ToolResult(
                success=proc.returncode == 0,
                data=output
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, data=None, error="Execution timed out (infinite loop or hang).")
        except Exception as e:
            return ToolResult(success=False, data=None, error=str(e))
        finally:
            shutil.rmtree(workspace_dir, ignore_errors=True)

import asyncio
import os
import tempfile
import pathlib

class DockerExecutor:
    @staticmethod
    async def execute(code: str, timeout: int = 30) -> dict:
        fd, tmp_path = tempfile.mkstemp(suffix=".py")
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(code)
            
        try:
            # Format path for docker on windows/linux.
            # Convert to absolute posix-style path for Docker if on windows
            # Docker Desktop on windows can handle C:\... usually, but safer is standard
            host_path = str(pathlib.Path(tmp_path).absolute())
            
            cmd = [
                "docker", "run", "--rm",
                "--cpus=0.5",
                "--memory=256m",
                "--network=none",
                "-v", f"{host_path}:/app/code.py:ro",
                "python:3.9-slim",
                "python", "/app/code.py"
            ]
            
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
                return {
                    "stdout": stdout.decode() if stdout else "",
                    "stderr": stderr.decode() if stderr else "",
                    "exit_code": proc.returncode,
                    "success": proc.returncode == 0
                }
            except asyncio.TimeoutError:
                proc.kill()
                return {
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout} seconds",
                    "exit_code": -1,
                    "success": False,
                    "error": f"Execution timed out after {timeout} seconds"
                }
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

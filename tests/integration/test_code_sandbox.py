import pytest
import asyncio
from backend.tools.code_execution import CodeSandboxTool

@pytest.mark.asyncio
async def test_sandbox_infinite_loop():
    tool = CodeSandboxTool()
    code = "while True: pass"
    
    result = await tool.execute(code=code)
    assert result.success is False
    assert "timed out" in result.error

@pytest.mark.asyncio
async def test_sandbox_env_isolation():
    tool = CodeSandboxTool()
    code = "import os; print(os.environ.get('SECRET_KEY', 'MISSING'))"
    
    result = await tool.execute(code=code)
    # The empty environment should prevent reading the host's SECRET_KEY
    assert result.success is True
    assert "MISSING" in result.data

@pytest.mark.asyncio
async def test_sandbox_valid_code():
    tool = CodeSandboxTool()
    code = "print('Hello World')"
    
    result = await tool.execute(code=code)
    assert result.success is True
    assert "Hello World" in result.data

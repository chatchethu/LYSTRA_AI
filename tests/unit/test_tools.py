"""
Unit tests for the Tool System
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestCalculatorTool:
    """Tests for the calculator tool."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_simple_addition(self):
        from backend.tools.calculator import CalculatorTool
        tool = CalculatorTool()
        result = await tool.execute(expression="2 + 2")
        assert result.success is True
        assert "4" in str(result.data)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_complex_expression(self):
        from backend.tools.calculator import CalculatorTool
        tool = CalculatorTool()
        result = await tool.execute(expression="(10 * 5) / 2 + 3")
        assert result.success is True
        assert "28" in str(result.data)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_expression(self):
        from backend.tools.calculator import CalculatorTool
        tool = CalculatorTool()
        result = await tool.execute(expression="import os; os.system('rm -rf /')")
        assert result.success is False


class TestDateTimeTool:
    """Tests for the datetime tool."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_current_time(self):
        from backend.tools.datetime_tool import DateTimeTool
        tool = DateTimeTool()
        result = await tool.execute(timezone="UTC")
        assert result.success is True
        assert "datetime" in result.data or "current_time" in str(result.data)

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_invalid_timezone(self):
        from backend.tools.datetime_tool import DateTimeTool
        tool = DateTimeTool()
        result = await tool.execute(timezone="Invalid/Timezone")
        # Should handle gracefully
        assert result is not None


class TestToolRegistry:
    """Tests for the tool registry."""

    def test_register_and_retrieve_tool(self):
        from backend.tools.registry import ToolRegistry
        from backend.tools.calculator import CalculatorTool

        registry = ToolRegistry()
        tool = CalculatorTool()
        registry.register(tool)

        retrieved = registry.get("calculate")
        assert retrieved is not None
        assert retrieved.name == "calculate"

    def test_list_tools(self):
        from backend.tools.registry import ToolRegistry
        from backend.tools.calculator import CalculatorTool
        from backend.tools.datetime_tool import DateTimeTool

        registry = ToolRegistry()
        registry.register(CalculatorTool())
        registry.register(DateTimeTool())

        tools = registry.list_tools()
        assert len(tools) >= 2

    def test_get_llm_schemas(self):
        from backend.tools.registry import ToolRegistry
        from backend.tools.calculator import CalculatorTool

        registry = ToolRegistry()
        registry.register(CalculatorTool())

        schemas = registry.get_llm_tool_schemas()
        assert len(schemas) >= 1
        assert "type" in schemas[0]
        assert schemas[0]["type"] == "function"

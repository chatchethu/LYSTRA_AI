"""
Unit tests for LLM Gateway and Model Router
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from backend.llm.gateway import LLMGateway
from backend.llm.model_router import ModelRouter, TaskType


class TestModelRouter:
    """Tests for model selection based on task type."""

    def setup_method(self):
        self.router = ModelRouter()

    def test_chat_model_selection(self):
        model = self.router.get_model(TaskType.CHAT)
        assert model is not None
        assert isinstance(model, str)

    def test_code_model_selection(self):
        model = self.router.get_model(TaskType.CODE)
        assert model is not None

    def test_vision_model_selection(self):
        model = self.router.get_model(TaskType.VISION)
        assert model is not None

    def test_embedding_model_selection(self):
        model = self.router.get_model(TaskType.EMBEDDING)
        assert model is not None

    def test_all_task_types_have_models(self):
        for task_type in TaskType:
            model = self.router.get_model(task_type)
            assert model is not None, f"No model for task type: {task_type}"


class TestLLMGateway:
    """Tests for LLM Gateway."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_chat_delegates_to_provider(self):
        mock_provider = AsyncMock()
        mock_provider.chat = AsyncMock(return_value="Test response")

        gateway = LLMGateway(provider=mock_provider)
        result = await gateway.chat([{"role": "user", "content": "Hello"}])

        assert result == "Test response"
        mock_provider.chat.assert_called_once()

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_embed_delegates_to_provider(self):
        mock_provider = AsyncMock()
        mock_provider.embed = AsyncMock(return_value=[0.1, 0.2, 0.3])

        gateway = LLMGateway(provider=mock_provider)
        result = await gateway.embed("Test text")

        assert result == [0.1, 0.2, 0.3]
        mock_provider.embed.assert_called_once_with("Test text", "default", request_id=None, task_id=None, operation="embed")

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_health_check_returns_bool(self):
        mock_provider = AsyncMock()
        mock_provider.health_check = AsyncMock(return_value=True)

        gateway = LLMGateway(provider=mock_provider)
        result = await gateway.health_check()

        assert isinstance(result, bool)
        assert result is True

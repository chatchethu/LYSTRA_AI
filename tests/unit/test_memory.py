"""
Unit tests for the Memory System
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestShortTermMemory:
    """Tests for short-term conversation memory."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_add_and_retrieve_message(self):
        from backend.memory.short_term import ShortTermMemory
        memory = ShortTermMemory()
        await memory.add_message("user", "Hello!")
        await memory.add_message("assistant", "Hi there!")

        context = await memory.get_context()
        assert len(context) == 2
        assert context[0]["role"] == "user"
        assert context[1]["role"] == "assistant"

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_get_recent_messages(self):
        from backend.memory.short_term import ShortTermMemory
        memory = ShortTermMemory()
        for i in range(10):
            await memory.add_message("user", f"Message {i}")

        recent = await memory.get_recent(3)
        assert len(recent) == 3
        assert "Message 9" in recent[-1]["content"]

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_clear_memory(self):
        from backend.memory.short_term import ShortTermMemory
        memory = ShortTermMemory()
        await memory.add_message("user", "Hello")
        await memory.clear()

        context = await memory.get_context()
        assert len(context) == 0

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_token_count(self):
        from backend.memory.short_term import ShortTermMemory
        memory = ShortTermMemory()
        count = await memory.count_tokens("Hello world, this is a test.")
        assert count > 0
        assert isinstance(count, int)


class TestLongTermMemory:
    """Tests for long-term memory with mocked DB."""

    @pytest.mark.asyncio
    @pytest.mark.unit
    async def test_remember_and_recall(self):
        from backend.memory.long_term import LongTermMemory, MemoryCategory

        mock_db = AsyncMock()
        mock_vector_store = AsyncMock()
        mock_llm = AsyncMock()

        memory = LongTermMemory(db=mock_db, vector_store=mock_vector_store)

        # Mock the DB create to return a Memory-like object
        mock_memory_obj = MagicMock()
        mock_memory_obj.id = uuid4()
        mock_memory_obj.content = "I prefer dark mode"
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Test deduplicate returns False (no duplicate)
        mock_vector_store.search_text = AsyncMock(return_value=[])

        # The actual remember call
        with patch.object(memory, 'deduplicate', return_value=False):
            with patch.object(memory, '_create_memory', return_value=mock_memory_obj):
                result = await memory.remember(
                    user_id=uuid4(),
                    content="I prefer dark mode",
                    category=MemoryCategory.PREFERENCE,
                )
        assert result is not None

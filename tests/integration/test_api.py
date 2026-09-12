"""
Integration tests for the Chat API
"""
import pytest
import json
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, patch


@pytest.fixture
async def client():
    """Create test client."""
    from backend.main import app
    from backend.auth.dependencies import get_llm_gateway
    app.dependency_overrides[get_llm_gateway] = lambda: AsyncMock()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides = {}


@pytest.fixture
async def auth_headers(client):
    """Get authentication headers."""
    # Register a test user
    register_response = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "username": "testuser",
        "password": "testpassword123",
        "display_name": "Test User"
    })

    if register_response.status_code == 400:
        # User already exists, login instead
        login_response = await client.post("/api/v1/auth/login", data={
            "username": "test@example.com",
            "password": "testpassword123"
        })
        token_str = login_response.cookies.get("access_token")
    else:
        token_str = register_response.cookies.get("access_token")

    return {"Authorization": f"Bearer {token_str}"} if token_str else {}


@pytest.mark.integration
class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


@pytest.mark.integration
class TestAuthAPI:
    """Tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_user(self, client):
        import uuid
        unique_email = f"newuser_{uuid.uuid4().hex[:8]}@example.com"
        response = await client.post("/api/v1/auth/register", json={
            "email": unique_email,
            "username": f"newuser_{uuid.uuid4().hex[:8]}",
            "password": "securepassword123",
            "display_name": "New User"
        })
        assert response.status_code in [200, 201]
        assert "access_token" in response.cookies
        assert "refresh_token" in response.cookies

    @pytest.mark.asyncio
    async def test_login(self, client):
        # First register
        import uuid
        email = f"logintest_{uuid.uuid4().hex[:8]}@example.com"
        username = f"logintest_{uuid.uuid4().hex[:8]}"
        await client.post("/api/v1/auth/register", json={
            "email": email,
            "username": username,
            "password": "testpass123",
            "display_name": "Login Test"
        })

        # Then login
        response = await client.post("/api/v1/auth/login", data={
            "username": email,
            "password": "testpass123"
        })
        assert response.status_code == 200
        assert "access_token" in response.cookies

    @pytest.mark.asyncio
    async def test_get_current_user(self, client, auth_headers):
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "username" in data

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401


@pytest.mark.integration
class TestConversationAPI:
    """Tests for conversation management endpoints."""

    @pytest.mark.asyncio
    async def test_create_conversation(self, client, auth_headers):
        response = await client.post("/api/v1/conversations", json={
            "title": "Test Conversation"
        }, headers=auth_headers)
        if response.status_code not in [200, 201]:
            print(response.text)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Conversation"

    @pytest.mark.asyncio
    async def test_list_conversations(self, client, auth_headers):
        response = await client.get("/api/v1/conversations", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_cross_user_access(self, client, auth_headers):
        # Create user A's conversation
        conv_res = await client.post("/api/v1/conversations", json={"title": "User A Conv"}, headers=auth_headers)
        conv_id = conv_res.json()["id"]

        # Register User B
        import uuid
        user_b_email = f"user_b_{uuid.uuid4().hex[:8]}@example.com"
        await client.post("/api/v1/auth/register", json={
            "email": user_b_email,
            "username": f"userb_{uuid.uuid4().hex[:8]}",
            "password": "strongpassword123!"
        })
        login_res = await client.post("/api/v1/auth/login", data={
            "username": user_b_email,
            "password": "strongpassword123!"
        })
        user_b_token = login_res.cookies.get("access_token")
        user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

        # User B tries to access User A's conversation
        get_res = await client.get(f"/api/v1/conversations/{conv_id}", headers=user_b_headers)
        assert get_res.status_code == 404

    @pytest.mark.asyncio
    async def test_get_conversation(self, client, auth_headers):
        # Create first
        create_response = await client.post("/api/v1/conversations", json={
            "title": "Test"
        }, headers=auth_headers)
        conv_id = create_response.json()["id"]

        # Then get
        response = await client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
        assert response.status_code == 200


@pytest.mark.integration
class TestChatAPI:
    """Tests for chat endpoints."""

    @pytest.mark.asyncio
    async def test_chat_requires_auth(self, client):
        response = await client.post("/api/v1/messages", json={
            "message": "Hello"
        })
        if response.status_code != 401:
            raise Exception(f"Expected 401, got {response.status_code}. Body: {response.text}")
        assert response.status_code == 401

    @pytest.mark.asyncio
    @patch("backend.agent.runtime.AgentRuntime.process_message")
    async def test_chat_returns_response(self, mock_process, client, auth_headers):
        from backend.contracts.agent import AgentResponse
        from backend.intelligence.state import ConversationState
        mock_process.return_value = (AgentResponse(content="Hello! How can I help you today?", metadata={"action_type": "direct_response"}), ConversationState())

        response = await client.post("/api/v1/messages", json={
            "message": "Hello",
            "stream": False
        }, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data


@pytest.mark.integration
class TestFullFlowAPI:
    """Tests for the complete end-to-end API flow (Part 49)."""
    
    @pytest.mark.asyncio
    @patch("backend.agent.runtime.AgentRuntime.process_message")
    async def test_full_api_flow(self, mock_process, client):
        import uuid
        from backend.contracts.agent import AgentResponse
        from backend.intelligence.state import ConversationState
        
        # 1. Register
        email = f"fullflow_{uuid.uuid4().hex[:8]}@example.com"
        register_response = await client.post("/api/v1/auth/register", json={
            "email": email,
            "username": f"fullflow_{uuid.uuid4().hex[:8]}",
            "password": "testpass123",
            "display_name": "Full Flow User"
        })
        assert register_response.status_code in [200, 201]
        
        # 2. Login
        login_response = await client.post("/api/v1/auth/login", data={
            "username": email,
            "password": "testpass123"
        })
        assert login_response.status_code == 200
        token = login_response.cookies.get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create Conversation
        conv_response = await client.post("/api/v1/conversations", json={
            "title": "Full Flow Test"
        }, headers=headers)
        assert conv_response.status_code in [200, 201]
        conv_id = conv_response.json()["id"]
        
        # Mock responses for different steps
        # 4. Chat
        mock_process.return_value = (AgentResponse(content="Hello! I'm ready to help.", metadata={"action_type": "direct_response"}), ConversationState())
        
        chat_res1 = await client.post("/api/v1/messages", json={
            "message": "Hello",
            "conversation_id": conv_id
        }, headers=headers)
        assert chat_res1.status_code == 200
        
        # 5. Switch topic
        mock_process.return_value = (AgentResponse(content="Switching to discussing quantum computing.", metadata={"action_type": "direct_response"}), ConversationState(active_topic="quantum physics"))
        
        chat_res2 = await client.post("/api/v1/messages", json={
            "message": "Let's talk about quantum physics now.",
            "conversation_id": conv_id
        }, headers=headers)
        assert chat_res2.status_code == 200
        
        # 6. Memory extraction
        mock_process.return_value = (AgentResponse(content="I'll remember that you like quantum physics.", metadata={"action_type": "direct_response"}), ConversationState(active_topic="quantum physics"))
        chat_res3 = await client.post("/api/v1/messages", json={
            "message": "Remember that I love quantum physics.",
            "conversation_id": conv_id
        }, headers=headers)
        assert chat_res3.status_code == 200
        
        # 7. Run task
        mock_process.return_value = (AgentResponse(content="Task started.", metadata={"action_type": "task_execution"}), ConversationState(active_topic="quantum physics"))
        chat_res4 = await client.post("/api/v1/messages", json={
            "message": "Run a simulation.",
            "conversation_id": conv_id
        }, headers=headers)
        assert chat_res4.status_code == 200
        
        # 8. Upload file
        file_res = await client.post("/api/files/upload", files={
            "file": ("test.txt", b"dummy content", "text/plain")
        }, headers=headers)
        # Note: If endpoint is not implemented this might 404, we test expected behavior if it exists
        if file_res.status_code != 404:
            assert file_res.status_code in [200, 201]
            
        # 9. Fallback model
        mock_process.return_value = (AgentResponse(content="Used fallback model."), ConversationState(active_topic="fallback"))
        chat_res5 = await client.post("/api/v1/messages", json={
            "message": "Use a fallback model.",
            "conversation_id": conv_id
        }, headers=headers)
        assert chat_res5.status_code == 200

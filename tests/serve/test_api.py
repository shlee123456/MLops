"""Tests for API endpoints"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns API info"""
    response = await client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "MLOps Chatbot API"
    assert data["status"] == "running"
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_health_check_no_vllm(client: AsyncClient):
    """Test health check when vLLM is not connected"""
    with patch("src.serve.routers.health.get_vllm_client", return_value=None):
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["vllm_connected"] is False


@pytest.mark.asyncio
async def test_health_check_with_vllm(client: AsyncClient):
    """Test health check when vLLM is connected"""
    mock_client = MagicMock()
    mock_client.health_check.return_value = True
    mock_client.list_models.return_value = ["test-model"]

    with patch("src.serve.routers.health.get_vllm_client", return_value=mock_client):
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["vllm_connected"] is True
    assert "test-model" in data["available_models"]


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    """Test metrics endpoint"""
    response = await client.get("/metrics")

    assert response.status_code == 200
    data = response.json()
    assert "requests_total" in data


@pytest.mark.asyncio
async def test_list_models(client: AsyncClient):
    """Test list models endpoint"""
    mock_client = MagicMock()
    mock_client.list_models.return_value = ["model-1", "model-2"]

    with patch("src.serve.routers.dependency.get_vllm_client", return_value=mock_client):
        response = await client.get("/v1/models")

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "list"
    assert len(data["data"]) == 2


@pytest.mark.asyncio
async def test_create_chat_session(client: AsyncClient):
    """Test creating a chat session"""
    response = await client.post(
        "/v1/chats",
        json={"title": "Test Chat", "model": "test-model"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Chat"
    assert data["model"] == "test-model"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_chat_sessions(client: AsyncClient):
    """Test listing chat sessions"""
    # Create some chats first
    await client.post("/v1/chats", json={"title": "Chat 1"})
    await client.post("/v1/chats", json={"title": "Chat 2"})

    response = await client.get("/v1/chats")

    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_chat_session(client: AsyncClient):
    """Test getting a specific chat session"""
    # Create a chat
    create_response = await client.post("/v1/chats", json={"title": "Test Chat"})
    chat_id = create_response.json()["id"]

    # Get the chat
    response = await client.get(f"/v1/chats/{chat_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == chat_id
    assert data["title"] == "Test Chat"


@pytest.mark.asyncio
async def test_get_chat_session_not_found(client: AsyncClient):
    """Test getting a non-existent chat session"""
    response = await client.get("/v1/chats/non-existent-id")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_chat_session(client: AsyncClient):
    """Test deleting a chat session"""
    # Create a chat
    create_response = await client.post("/v1/chats", json={"title": "To Delete"})
    chat_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(f"/v1/chats/{chat_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = await client.get(f"/v1/chats/{chat_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_chat_completion(client: AsyncClient, mock_vllm_response):
    """Test chat completion endpoint"""
    mock_client = MagicMock()
    mock_client.chat_completion.return_value = mock_vllm_response

    with patch("src.serve.routers.dependency.get_vllm_client", return_value=mock_client):
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "temperature": 0.7,
                "max_tokens": 100,
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "This is a test response from the model."
    assert data["model"] == "test-model"
    assert "usage" in data


@pytest.mark.asyncio
async def test_chat_completion_with_session(client: AsyncClient, mock_vllm_response):
    """Test chat completion with session persistence"""
    # Create a chat session
    create_response = await client.post("/v1/chats", json={"title": "Test"})
    session_id = create_response.json()["id"]

    mock_client = MagicMock()
    mock_client.chat_completion.return_value = mock_vllm_response

    with patch("src.serve.routers.dependency.get_vllm_client", return_value=mock_client):
        response = await client.post(
            "/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "session_id": session_id,
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id

    # Verify messages were saved
    messages_response = await client.get(f"/v1/chats/{session_id}/messages")
    messages = messages_response.json()
    assert len(messages) == 2  # user + assistant


@pytest.mark.asyncio
async def test_completion_endpoint(client: AsyncClient):
    """Test text completion endpoint"""
    mock_client = MagicMock()
    mock_client.completion.return_value = {
        "content": "Completed text",
        "model": "test-model",
        "usage": {"total_tokens": 10},
    }

    with patch("src.serve.routers.dependency.get_vllm_client", return_value=mock_client):
        response = await client.post(
            "/v1/completions",
            json={
                "prompt": "Once upon a time",
                "max_tokens": 50,
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Completed text"

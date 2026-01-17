"""
vLLM Integration Tests

vLLM 서버가 실행 중일 때만 테스트 실행
GPU 환경이 없으면 자동으로 스킵
"""

import os
import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

# vLLM 서버 URL (환경 변수 또는 기본값)
VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")


def is_vllm_running() -> bool:
    """Check if vLLM server is running"""
    try:
        response = httpx.get(
            f"{VLLM_BASE_URL.replace('/v1', '')}/health",
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


# Skip marker for tests requiring vLLM server
requires_vllm = pytest.mark.skipif(
    not is_vllm_running(),
    reason="vLLM server not running. Start with: python src/serve/01_vllm_server.py"
)


class TestVLLMIntegration:
    """vLLM Integration Tests (requires running vLLM server)"""

    @requires_vllm
    def test_vllm_health_check(self):
        """Test vLLM server health check"""
        response = httpx.get(
            f"{VLLM_BASE_URL.replace('/v1', '')}/health",
            timeout=10
        )
        assert response.status_code == 200

    @requires_vllm
    def test_vllm_list_models(self):
        """Test vLLM model listing"""
        response = httpx.get(
            f"{VLLM_BASE_URL}/models",
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0

    @requires_vllm
    def test_vllm_chat_completion(self):
        """Test vLLM chat completion"""
        response = httpx.post(
            f"{VLLM_BASE_URL}/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "Hello, say hi back in one word."}
                ],
                "max_tokens": 10,
                "temperature": 0.1
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert "message" in data["choices"][0]
        assert "content" in data["choices"][0]["message"]

    @requires_vllm
    def test_vllm_completion(self):
        """Test vLLM text completion"""
        response = httpx.post(
            f"{VLLM_BASE_URL}/completions",
            json={
                "prompt": "The capital of France is",
                "max_tokens": 5,
                "temperature": 0.1
            },
            timeout=60
        )
        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert "text" in data["choices"][0]


class TestVLLMClientMock:
    """vLLM Client tests with mocking (no server required)"""

    def test_vllm_client_initialization(self):
        """Test VLLMClient initialization"""
        import sys
        sys.path.insert(0, "src/serve")

        from src.serve.vllm_client import VLLMClient

        client = VLLMClient(base_url="http://localhost:9999/v1")
        assert client.base_url == "http://localhost:9999/v1"
        assert client.timeout == 60

    @patch('openai.OpenAI')
    def test_vllm_client_list_models_mock(self, mock_openai):
        """Test list_models with mock"""
        import sys
        sys.path.insert(0, "src/serve")

        from src.serve.vllm_client import VLLMClient

        # Mock model response
        mock_model = MagicMock()
        mock_model.id = "test-model"
        mock_models = MagicMock()
        mock_models.data = [mock_model]
        mock_openai.return_value.models.list.return_value = mock_models

        client = VLLMClient(base_url="http://localhost:9999/v1")
        models = client.list_models()

        assert "test-model" in models

    @patch('openai.OpenAI')
    def test_vllm_client_chat_completion_mock(self, mock_openai):
        """Test chat_completion with mock"""
        import sys
        sys.path.insert(0, "src/serve")

        from src.serve.vllm_client import VLLMClient

        # Mock models
        mock_model = MagicMock()
        mock_model.id = "test-model"
        mock_models = MagicMock()
        mock_models.data = [mock_model]
        mock_openai.return_value.models.list.return_value = mock_models

        # Mock chat completion response
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 5
        mock_usage.total_tokens = 15

        mock_message = MagicMock()
        mock_message.content = "Hello!"

        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_choice.finish_reason = "stop"

        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.model = "test-model"
        mock_response.usage = mock_usage

        mock_openai.return_value.chat.completions.create.return_value = mock_response

        client = VLLMClient(base_url="http://localhost:9999/v1")
        response = client.chat_completion(
            messages=[{"role": "user", "content": "Hi"}],
            temperature=0.7
        )

        assert response["content"] == "Hello!"
        assert response["model"] == "test-model"
        assert response["usage"]["total_tokens"] == 15

    @patch('openai.OpenAI')
    def test_vllm_client_health_check_mock(self, mock_openai):
        """Test health_check with mock"""
        import sys
        sys.path.insert(0, "src/serve")

        from src.serve.vllm_client import VLLMClient

        # Mock model response for health check
        mock_model = MagicMock()
        mock_model.id = "test-model"
        mock_models = MagicMock()
        mock_models.data = [mock_model]
        mock_openai.return_value.models.list.return_value = mock_models

        client = VLLMClient(base_url="http://localhost:9999/v1")
        assert client.health_check() is True


class TestFastAPIWithVLLM:
    """Test FastAPI server integration with vLLM"""

    @requires_vllm
    @pytest.mark.asyncio
    async def test_fastapi_chat_with_vllm(self):
        """Test FastAPI chat completion with real vLLM"""
        async with httpx.AsyncClient() as client:
            # Assuming FastAPI server is running on 8080
            try:
                response = await client.post(
                    "http://localhost:8080/v1/chat/completions",
                    json={
                        "messages": [
                            {"role": "user", "content": "Say hello"}
                        ],
                        "max_tokens": 10
                    },
                    timeout=60
                )
                if response.status_code == 200:
                    data = response.json()
                    assert "choices" in data
            except httpx.ConnectError:
                pytest.skip("FastAPI server not running")


if __name__ == "__main__":
    # Quick check if vLLM is running
    if is_vllm_running():
        print("✓ vLLM server is running")
        print("  Running integration tests...")
        pytest.main([__file__, "-v", "-k", "Integration"])
    else:
        print("⚠ vLLM server is not running")
        print("  Running mock tests only...")
        pytest.main([__file__, "-v", "-k", "Mock"])

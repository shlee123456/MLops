"""
API Tests

FastAPI 엔드포인트 테스트
"""

import pytest
from httpx import AsyncClient


# ============================================================
# 공통 엔드포인트 테스트
# ============================================================

@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    """루트 엔드포인트 테스트"""
    response = await client.get("/")
    assert response.status_code == 200

    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["status"] == "running"
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """헬스체크 테스트"""
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "healthy"
    assert data["vllm_connected"] is True
    assert "available_models" in data
    assert data["database_connected"] is True


@pytest.mark.asyncio
async def test_list_models(client: AsyncClient):
    """모델 목록 테스트"""
    response = await client.get("/v1/models")
    assert response.status_code == 200

    data = response.json()
    assert data["object"] == "list"
    assert "data" in data
    assert len(data["data"]) > 0
    assert data["data"][0]["id"] == "test-model"


# ============================================================
# Conversation 테스트
# ============================================================

@pytest.mark.asyncio
async def test_create_conversation(client: AsyncClient):
    """대화 생성 테스트"""
    response = await client.post(
        "/v1/conversations",
        json={"title": "테스트 대화"}
    )
    assert response.status_code == 201

    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "테스트 대화"


@pytest.mark.asyncio
async def test_list_conversations(client: AsyncClient):
    """대화 목록 테스트"""
    # 먼저 대화 생성
    await client.post("/v1/conversations", json={"title": "대화 1"})
    await client.post("/v1/conversations", json={"title": "대화 2"})

    response = await client.get("/v1/conversations")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.asyncio
async def test_get_conversation(client: AsyncClient):
    """대화 상세 조회 테스트"""
    # 먼저 대화 생성
    create_response = await client.post(
        "/v1/conversations",
        json={"title": "상세 조회 테스트"}
    )
    conversation_id = create_response.json()["id"]

    response = await client.get(f"/v1/conversations/{conversation_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == conversation_id
    assert data["title"] == "상세 조회 테스트"
    assert "messages" in data


@pytest.mark.asyncio
async def test_get_conversation_not_found(client: AsyncClient):
    """존재하지 않는 대화 조회 테스트"""
    response = await client.get("/v1/conversations/99999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_conversation(client: AsyncClient):
    """대화 삭제 테스트"""
    # 먼저 대화 생성
    create_response = await client.post(
        "/v1/conversations",
        json={"title": "삭제 테스트"}
    )
    conversation_id = create_response.json()["id"]

    # 삭제
    response = await client.delete(f"/v1/conversations/{conversation_id}")
    assert response.status_code == 204

    # 삭제 확인
    get_response = await client.get(f"/v1/conversations/{conversation_id}")
    assert get_response.status_code == 404


# ============================================================
# LLM Config 테스트
# ============================================================

@pytest.mark.asyncio
async def test_create_llm_config(client: AsyncClient):
    """LLM 설정 생성 테스트"""
    response = await client.post(
        "/v1/llm-configs",
        json={
            "name": "테스트 설정",
            "model_name": "test-model",
            "temperature": 0.8,
            "max_tokens": 1024,
        }
    )
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "테스트 설정"
    assert data["model_name"] == "test-model"
    assert data["temperature"] == 0.8
    assert data["max_tokens"] == 1024


@pytest.mark.asyncio
async def test_list_llm_configs(client: AsyncClient):
    """LLM 설정 목록 테스트"""
    # 먼저 설정 생성
    await client.post(
        "/v1/llm-configs",
        json={"name": "설정 1", "model_name": "model-1"}
    )

    response = await client.get("/v1/llm-configs")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# ============================================================
# Chat Completion 테스트
# ============================================================

@pytest.mark.asyncio
async def test_chat_completion(client: AsyncClient):
    """채팅 완성 테스트"""
    response = await client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {"role": "user", "content": "안녕하세요"}
            ],
            "temperature": 0.7,
            "max_tokens": 512,
        }
    )
    assert response.status_code == 200

    data = response.json()
    assert "content" in data
    assert data["content"] == "테스트 응답입니다."
    assert data["model"] == "test-model"
    assert "usage" in data
    assert data["usage"]["total_tokens"] == 30


@pytest.mark.asyncio
async def test_chat_completion_without_save(client: AsyncClient):
    """대화 저장 없이 채팅 완성 테스트"""
    response = await client.post(
        "/v1/chat/completions",
        json={
            "messages": [
                {"role": "user", "content": "테스트"}
            ],
            "save_conversation": False,
        }
    )
    assert response.status_code == 200

    data = response.json()
    assert data["conversation_id"] is None

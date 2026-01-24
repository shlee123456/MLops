"""
LLM Config API Tests

LLM Config CRUD 엔드포인트 통합 테스트
"""

import pytest
from httpx import AsyncClient


# ============================================================
# US-002: LLM Config 생성 테스트
# ============================================================

@pytest.mark.asyncio
async def test_create_llm_config_all_fields(client: AsyncClient):
    """모든 필드 포함 생성 시 201 응답 및 필드 일치 확인"""
    payload = {
        "name": "full-config-test",
        "model_name": "llama3-8b",
        "system_prompt": "You are a helpful assistant.",
        "temperature": 0.5,
        "max_tokens": 2048,
        "top_p": 0.95,
        "is_default": False,
    }
    response = await client.post("/v1/llm-configs", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == payload["name"]
    assert data["model_name"] == payload["model_name"]
    assert data["system_prompt"] == payload["system_prompt"]
    assert data["temperature"] == payload["temperature"]
    assert data["max_tokens"] == payload["max_tokens"]
    assert data["top_p"] == payload["top_p"]
    assert data["is_default"] == payload["is_default"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_llm_config_required_fields_only(client: AsyncClient):
    """필수 필드만으로 생성 시 기본값 적용 확인"""
    payload = {
        "name": "minimal-config-test",
        "model_name": "llama3-8b",
    }
    response = await client.post("/v1/llm-configs", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["name"] == "minimal-config-test"
    assert data["model_name"] == "llama3-8b"
    assert data["temperature"] == 0.7  # 기본값
    assert data["max_tokens"] == 512  # 기본값
    assert data["top_p"] == 0.9  # 기본값
    assert data["is_default"] is False  # 기본값
    assert data["system_prompt"] is None  # 기본값


@pytest.mark.asyncio
async def test_create_llm_config_missing_name(client: AsyncClient):
    """필수 필드 name 누락 시 422 에러"""
    payload = {
        "model_name": "llama3-8b",
    }
    response = await client.post("/v1/llm-configs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_llm_config_missing_model_name(client: AsyncClient):
    """필수 필드 model_name 누락 시 422 에러"""
    payload = {
        "name": "missing-model-test",
    }
    response = await client.post("/v1/llm-configs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_llm_config_temperature_too_high(client: AsyncClient):
    """temperature > 2.0 시 422 에러"""
    payload = {
        "name": "temp-high-test",
        "model_name": "llama3-8b",
        "temperature": 2.5,
    }
    response = await client.post("/v1/llm-configs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_llm_config_temperature_too_low(client: AsyncClient):
    """temperature < 0.0 시 422 에러"""
    payload = {
        "name": "temp-low-test",
        "model_name": "llama3-8b",
        "temperature": -0.1,
    }
    response = await client.post("/v1/llm-configs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_llm_config_max_tokens_too_high(client: AsyncClient):
    """max_tokens > 4096 시 422 에러"""
    payload = {
        "name": "tokens-high-test",
        "model_name": "llama3-8b",
        "max_tokens": 5000,
    }
    response = await client.post("/v1/llm-configs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_llm_config_max_tokens_too_low(client: AsyncClient):
    """max_tokens < 1 시 422 에러"""
    payload = {
        "name": "tokens-low-test",
        "model_name": "llama3-8b",
        "max_tokens": 0,
    }
    response = await client.post("/v1/llm-configs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_llm_config_top_p_too_high(client: AsyncClient):
    """top_p > 1.0 시 422 에러"""
    payload = {
        "name": "top-p-high-test",
        "model_name": "llama3-8b",
        "top_p": 1.5,
    }
    response = await client.post("/v1/llm-configs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_llm_config_top_p_too_low(client: AsyncClient):
    """top_p < 0.0 시 422 에러"""
    payload = {
        "name": "top-p-low-test",
        "model_name": "llama3-8b",
        "top_p": -0.1,
    }
    response = await client.post("/v1/llm-configs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_llm_config_duplicate_name(client: AsyncClient):
    """name 중복 생성 시 409 에러"""
    payload = {
        "name": "duplicate-name-test",
        "model_name": "llama3-8b",
    }
    # 첫 번째 생성
    response1 = await client.post("/v1/llm-configs", json=payload)
    assert response1.status_code == 201

    # 같은 이름으로 두 번째 생성
    response2 = await client.post("/v1/llm-configs", json=payload)
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"]

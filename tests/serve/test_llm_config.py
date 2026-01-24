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


# ============================================================
# US-003: LLM Config 수정/삭제 테스트
# ============================================================

@pytest.mark.asyncio
async def test_update_llm_config_partial(client: AsyncClient):
    """부분 업데이트 - 변경하지 않는 필드는 유지"""
    # 생성
    payload = {
        "name": "update-partial-test",
        "model_name": "llama3-8b",
        "temperature": 0.5,
        "max_tokens": 1024,
        "top_p": 0.8,
    }
    create_resp = await client.post("/v1/llm-configs", json=payload)
    assert create_resp.status_code == 201
    config_id = create_resp.json()["id"]

    # temperature만 수정
    update_resp = await client.put(
        f"/v1/llm-configs/{config_id}",
        json={"temperature": 1.0},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["temperature"] == 1.0
    # 나머지 필드는 유지
    assert data["name"] == "update-partial-test"
    assert data["model_name"] == "llama3-8b"
    assert data["max_tokens"] == 1024
    assert data["top_p"] == 0.8


@pytest.mark.asyncio
async def test_update_llm_config_multiple_fields(client: AsyncClient):
    """여러 필드 동시 업데이트"""
    create_resp = await client.post("/v1/llm-configs", json={
        "name": "update-multi-test",
        "model_name": "llama3-8b",
    })
    config_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/v1/llm-configs/{config_id}",
        json={
            "model_name": "llama3-70b",
            "system_prompt": "New prompt",
            "temperature": 1.5,
            "max_tokens": 4096,
        },
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["model_name"] == "llama3-70b"
    assert data["system_prompt"] == "New prompt"
    assert data["temperature"] == 1.5
    assert data["max_tokens"] == 4096


@pytest.mark.asyncio
async def test_update_llm_config_not_found(client: AsyncClient):
    """존재하지 않는 ID 수정 시 404"""
    response = await client.put(
        "/v1/llm-configs/99999",
        json={"temperature": 1.0},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_update_llm_config_validation_error(client: AsyncClient):
    """수정 시 유효성 검증 실패 (temperature 범위 초과)"""
    create_resp = await client.post("/v1/llm-configs", json={
        "name": "update-validation-test",
        "model_name": "llama3-8b",
    })
    config_id = create_resp.json()["id"]

    response = await client.put(
        f"/v1/llm-configs/{config_id}",
        json={"temperature": 3.0},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_llm_config(client: AsyncClient):
    """LLM Config 삭제 성공"""
    create_resp = await client.post("/v1/llm-configs", json={
        "name": "delete-test",
        "model_name": "llama3-8b",
    })
    config_id = create_resp.json()["id"]

    # 삭제
    delete_resp = await client.delete(f"/v1/llm-configs/{config_id}")
    assert delete_resp.status_code == 204

    # 삭제 확인
    get_resp = await client.get(f"/v1/llm-configs/{config_id}")
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_llm_config_not_found(client: AsyncClient):
    """존재하지 않는 ID 삭제 시 404"""
    response = await client.delete("/v1/llm-configs/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_llm_config_nullifies_conversation_fk(client: AsyncClient):
    """삭제 시 참조 Conversation의 llm_config_id가 NULL 처리"""
    # Config 생성
    config_resp = await client.post("/v1/llm-configs", json={
        "name": "fk-null-test",
        "model_name": "llama3-8b",
    })
    config_id = config_resp.json()["id"]

    # Conversation 생성 (llm_config_id 참조)
    conv_resp = await client.post("/v1/conversations", json={
        "title": "FK test conversation",
        "llm_config_id": config_id,
    })
    assert conv_resp.status_code == 201
    conv_id = conv_resp.json()["id"]

    # Config 삭제
    delete_resp = await client.delete(f"/v1/llm-configs/{config_id}")
    assert delete_resp.status_code == 204

    # Conversation의 llm_config_id가 NULL인지 확인
    conv_detail = await client.get(f"/v1/conversations/{conv_id}")
    assert conv_detail.status_code == 200
    assert conv_detail.json()["llm_config_id"] is None


# ============================================================
# US-003: LLM Config 조회 테스트
# ============================================================

@pytest.mark.asyncio
async def test_list_llm_configs(client: AsyncClient):
    """목록 조회 - 생성한 설정 포함 확인"""
    # 생성
    await client.post("/v1/llm-configs", json={
        "name": "list-test-a",
        "model_name": "llama3-8b",
    })
    await client.post("/v1/llm-configs", json={
        "name": "list-test-b",
        "model_name": "llama3-70b",
    })

    response = await client.get("/v1/llm-configs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    names = [c["name"] for c in data]
    assert "list-test-a" in names
    assert "list-test-b" in names


@pytest.mark.asyncio
async def test_list_llm_configs_sorted_by_name(client: AsyncClient):
    """목록이 name 순으로 정렬되어 반환"""
    response = await client.get("/v1/llm-configs")
    assert response.status_code == 200
    data = response.json()
    names = [c["name"] for c in data]
    assert names == sorted(names)


@pytest.mark.asyncio
async def test_get_llm_config_by_id(client: AsyncClient):
    """특정 설정 조회 시 모든 필드 일치 확인"""
    payload = {
        "name": "get-by-id-test",
        "model_name": "llama3-8b",
        "system_prompt": "Test prompt",
        "temperature": 0.3,
        "max_tokens": 256,
        "top_p": 0.85,
        "is_default": False,
    }
    create_resp = await client.post("/v1/llm-configs", json=payload)
    config_id = create_resp.json()["id"]

    get_resp = await client.get(f"/v1/llm-configs/{config_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["name"] == payload["name"]
    assert data["model_name"] == payload["model_name"]
    assert data["system_prompt"] == payload["system_prompt"]
    assert data["temperature"] == payload["temperature"]
    assert data["max_tokens"] == payload["max_tokens"]
    assert data["top_p"] == payload["top_p"]


@pytest.mark.asyncio
async def test_get_llm_config_not_found(client: AsyncClient):
    """존재하지 않는 ID 조회 시 404"""
    response = await client.get("/v1/llm-configs/99999")
    assert response.status_code == 404


# ============================================================
# US-004: is_default 중복 방지 로직 테스트
# ============================================================

@pytest.mark.asyncio
async def test_create_default_clears_existing(client: AsyncClient):
    """새 Config를 is_default=true로 생성하면 기존 default가 false로 변경"""
    # 첫 번째 default 생성
    resp1 = await client.post("/v1/llm-configs", json={
        "name": "default-first",
        "model_name": "llama3-8b",
        "is_default": True,
    })
    assert resp1.status_code == 201
    id1 = resp1.json()["id"]
    assert resp1.json()["is_default"] is True

    # 두 번째 default 생성 → 첫 번째가 해제되어야 함
    resp2 = await client.post("/v1/llm-configs", json={
        "name": "default-second",
        "model_name": "llama3-8b",
        "is_default": True,
    })
    assert resp2.status_code == 201
    assert resp2.json()["is_default"] is True

    # 첫 번째 확인 → is_default가 False
    check_resp = await client.get(f"/v1/llm-configs/{id1}")
    assert check_resp.json()["is_default"] is False


@pytest.mark.asyncio
async def test_update_default_clears_existing(client: AsyncClient):
    """기존 Config를 is_default=true로 수정해도 기존 default가 해제"""
    # default Config 생성
    resp1 = await client.post("/v1/llm-configs", json={
        "name": "update-default-orig",
        "model_name": "llama3-8b",
        "is_default": True,
    })
    id1 = resp1.json()["id"]

    # 비-default Config 생성
    resp2 = await client.post("/v1/llm-configs", json={
        "name": "update-default-new",
        "model_name": "llama3-8b",
        "is_default": False,
    })
    id2 = resp2.json()["id"]

    # 두 번째를 default로 수정
    update_resp = await client.put(
        f"/v1/llm-configs/{id2}",
        json={"is_default": True},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["is_default"] is True

    # 첫 번째 확인 → is_default가 False
    check_resp = await client.get(f"/v1/llm-configs/{id1}")
    assert check_resp.json()["is_default"] is False


@pytest.mark.asyncio
async def test_set_default_when_none_exists(client: AsyncClient):
    """is_default=true인 Config가 없는 상태에서 새로 설정 가능"""
    # 비-default Config 생성
    resp = await client.post("/v1/llm-configs", json={
        "name": "set-default-fresh",
        "model_name": "llama3-8b",
        "is_default": False,
    })
    config_id = resp.json()["id"]

    # default로 수정
    update_resp = await client.put(
        f"/v1/llm-configs/{config_id}",
        json={"is_default": True},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["is_default"] is True


@pytest.mark.asyncio
async def test_only_one_default_in_list(client: AsyncClient):
    """목록 조회 시 is_default=true가 항상 0~1개"""
    response = await client.get("/v1/llm-configs")
    assert response.status_code == 200
    data = response.json()
    default_count = sum(1 for c in data if c["is_default"] is True)
    assert default_count <= 1


# ============================================================
# US-005: Admin UI를 통한 LLMConfig CRUD 테스트
# ============================================================

async def _admin_login(client: AsyncClient):
    """Admin 로그인 헬퍼"""
    import re
    login_page = await client.get("/admin/login")
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', login_page.text)
    if not match:
        match = re.search(r'value="([^"]+)"[^>]*name="csrf_token"', login_page.text)
    csrf_token = match.group(1) if match else None

    data = {"username": "admin", "password": "changeme"}
    if csrf_token:
        data["csrf_token"] = csrf_token
    await client.post("/admin/login", data=data, follow_redirects=True)


@pytest.mark.asyncio
async def test_admin_llm_config_list(client: AsyncClient):
    """/admin/llm-config/list 페이지 접근 시 200 응답"""
    await _admin_login(client)
    response = await client.get("/admin/llm-config/list", follow_redirects=True)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_llm_config_create_page(client: AsyncClient):
    """/admin/llm-config/create 페이지 접근 가능"""
    await _admin_login(client)
    response = await client.get("/admin/llm-config/create", follow_redirects=True)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_llm_config_detail(client: AsyncClient):
    """/admin/llm-config/details/{id} 페이지에서 상세 정보 확인"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from src.serve.models.chat import LLMConfig
    from tests.serve.conftest import TEST_SYNC_DATABASE_URL

    # SQLAdmin은 sync 엔진을 사용하므로 직접 sync 세션으로 삽입
    engine = create_engine(TEST_SYNC_DATABASE_URL)
    with Session(engine) as session:
        config = LLMConfig(name="admin-detail-sync", model_name="llama3-8b", temperature=0.7, max_tokens=512, top_p=0.9, is_default=False)
        session.add(config)
        session.commit()
        config_id = config.id
    engine.dispose()

    await _admin_login(client)
    response = await client.get(
        f"/admin/llm-config/details/{config_id}", follow_redirects=True
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_llm_config_edit_page(client: AsyncClient):
    """/admin/llm-config/edit/{id} 페이지 접근 가능"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from src.serve.models.chat import LLMConfig
    from tests.serve.conftest import TEST_SYNC_DATABASE_URL

    engine = create_engine(TEST_SYNC_DATABASE_URL)
    with Session(engine) as session:
        config = LLMConfig(name="admin-edit-sync", model_name="llama3-8b", temperature=0.7, max_tokens=512, top_p=0.9, is_default=False)
        session.add(config)
        session.commit()
        config_id = config.id
    engine.dispose()

    await _admin_login(client)
    response = await client.get(
        f"/admin/llm-config/edit/{config_id}", follow_redirects=True
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_llm_config_search_by_name(client: AsyncClient):
    """name 필드로 검색 기능 동작 확인"""
    await _admin_login(client)
    response = await client.get(
        "/admin/llm-config/list?search=admin-detail", follow_redirects=True
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_llm_config_search_by_model(client: AsyncClient):
    """model_name 필드로 검색 기능 동작 확인"""
    await _admin_login(client)
    response = await client.get(
        "/admin/llm-config/list?search=llama3", follow_redirects=True
    )
    assert response.status_code == 200

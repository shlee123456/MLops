"""
Admin Tests

SQLAdmin 관리자 인터페이스 테스트
"""

import re

import pytest
from httpx import AsyncClient

from src.serve.admin.auth import create_access_token, verify_token


# ============================================================
# JWT 토큰 유닛 테스트
# ============================================================

def test_create_access_token():
    """JWT 토큰 생성 테스트"""
    token = create_access_token(data={"sub": "admin"})
    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0


def test_verify_token_valid():
    """유효한 토큰 검증 테스트"""
    token = create_access_token(data={"sub": "testuser"})
    username = verify_token(token)
    assert username == "testuser"


def test_verify_token_invalid():
    """유효하지 않은 토큰 검증 테스트"""
    result = verify_token("invalid-token")
    assert result is None


def test_verify_token_empty():
    """빈 토큰 검증 테스트"""
    result = verify_token("")
    assert result is None


# ============================================================
# Helper 함수
# ============================================================

def extract_csrf_token(html: str) -> str | None:
    """HTML에서 CSRF 토큰 추출"""
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    if match:
        return match.group(1)
    # 다른 형식 시도
    match = re.search(r'value="([^"]+)"[^>]*name="csrf_token"', html)
    return match.group(1) if match else None


# ============================================================
# Admin 페이지 접근 테스트
# ============================================================

@pytest.mark.asyncio
async def test_admin_redirect_without_auth(client: AsyncClient):
    """인증 없이 admin 접근 시 로그인 페이지로 리다이렉트"""
    response = await client.get("/admin/", follow_redirects=False)
    # 302 리다이렉트 또는 200 (로그인 페이지 표시)
    assert response.status_code in [200, 302, 303]


@pytest.mark.asyncio
async def test_admin_login_page(client: AsyncClient):
    """Admin 로그인 페이지 접근 테스트"""
    response = await client.get("/admin/login", follow_redirects=True)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_login_success(client: AsyncClient):
    """Admin 로그인 성공 테스트"""
    # 먼저 로그인 페이지에서 CSRF 토큰 획득
    login_page = await client.get("/admin/login")
    csrf_token = extract_csrf_token(login_page.text)

    data = {"username": "admin", "password": "changeme"}
    if csrf_token:
        data["csrf_token"] = csrf_token

    response = await client.post(
        "/admin/login",
        data=data,
        follow_redirects=False,
    )
    # 로그인 성공 시 리다이렉트
    assert response.status_code in [302, 303]


@pytest.mark.asyncio
async def test_admin_login_failure(client: AsyncClient):
    """Admin 로그인 실패 테스트 (잘못된 자격 증명)"""
    # 먼저 로그인 페이지에서 CSRF 토큰 획득
    login_page = await client.get("/admin/login")
    csrf_token = extract_csrf_token(login_page.text)

    data = {"username": "wrong", "password": "wrong"}
    if csrf_token:
        data["csrf_token"] = csrf_token

    response = await client.post(
        "/admin/login",
        data=data,
        follow_redirects=False,
    )
    # 실패 시 400 Bad Request (SQLAdmin 동작)
    assert response.status_code == 400
    assert "Invalid credentials" in response.text


@pytest.mark.asyncio
async def test_admin_logout(client: AsyncClient):
    """Admin 로그아웃 테스트"""
    # 먼저 로그인
    login_page = await client.get("/admin/login")
    csrf_token = extract_csrf_token(login_page.text)

    data = {"username": "admin", "password": "changeme"}
    if csrf_token:
        data["csrf_token"] = csrf_token

    await client.post(
        "/admin/login",
        data=data,
        follow_redirects=True,
    )

    # 로그아웃
    response = await client.get("/admin/logout", follow_redirects=False)
    assert response.status_code in [302, 303]


# ============================================================
# 커스텀 검색 테스트 (search_query)
# ============================================================

@pytest.mark.asyncio
async def test_conversation_search_by_id(client: AsyncClient):
    """대화 ID로 검색 테스트"""
    # 로그인
    login_page = await client.get("/admin/login")
    csrf_token = extract_csrf_token(login_page.text)
    data = {"username": "admin", "password": "changeme"}
    if csrf_token:
        data["csrf_token"] = csrf_token
    await client.post("/admin/login", data=data, follow_redirects=True)

    # 검색 쿼리 파라미터로 ID 검색
    response = await client.get("/admin/conversation/list?search=1", follow_redirects=True)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_conversation_search_by_title(client: AsyncClient):
    """대화 제목으로 검색 테스트"""
    # 로그인
    login_page = await client.get("/admin/login")
    csrf_token = extract_csrf_token(login_page.text)
    data = {"username": "admin", "password": "changeme"}
    if csrf_token:
        data["csrf_token"] = csrf_token
    await client.post("/admin/login", data=data, follow_redirects=True)

    # 제목 검색
    response = await client.get("/admin/conversation/list?search=test", follow_redirects=True)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_message_search_by_conversation_id(client: AsyncClient):
    """메시지 conversation_id로 검색 테스트"""
    # 로그인
    login_page = await client.get("/admin/login")
    csrf_token = extract_csrf_token(login_page.text)
    data = {"username": "admin", "password": "changeme"}
    if csrf_token:
        data["csrf_token"] = csrf_token
    await client.post("/admin/login", data=data, follow_redirects=True)

    # conversation_id로 검색
    response = await client.get("/admin/chat-message/list?search=1", follow_redirects=True)
    assert response.status_code == 200


# ============================================================
# BaseView 테스트 (커스텀 대시보드)
# ============================================================

@pytest.mark.asyncio
async def test_system_status_view(client: AsyncClient):
    """시스템 상태 대시보드 테스트"""
    # 로그인
    login_page = await client.get("/admin/login")
    csrf_token = extract_csrf_token(login_page.text)
    data = {"username": "admin", "password": "changeme"}
    if csrf_token:
        data["csrf_token"] = csrf_token
    await client.post("/admin/login", data=data, follow_redirects=True)

    # 시스템 상태 페이지 접근
    response = await client.get("/admin/system-status", follow_redirects=True)
    assert response.status_code == 200
    # 메모리 정보가 포함되어 있는지 확인
    assert "메모리" in response.text or "memory" in response.text.lower()


@pytest.mark.asyncio
async def test_message_statistics_view_get(client: AsyncClient):
    """메시지 통계 대시보드 GET 테스트"""
    # 로그인
    login_page = await client.get("/admin/login")
    csrf_token = extract_csrf_token(login_page.text)
    data = {"username": "admin", "password": "changeme"}
    if csrf_token:
        data["csrf_token"] = csrf_token
    await client.post("/admin/login", data=data, follow_redirects=True)

    # 메시지 통계 페이지 접근
    response = await client.get("/admin/message-statistics", follow_redirects=True)
    assert response.status_code == 200
    # 통계 정보 키워드 확인
    assert "통계" in response.text or "메시지" in response.text


@pytest.mark.asyncio
async def test_message_statistics_view_post(client: AsyncClient):
    """메시지 통계 대시보드 POST (날짜 필터) 테스트"""
    # 로그인
    login_page = await client.get("/admin/login")
    csrf_token = extract_csrf_token(login_page.text)
    data = {"username": "admin", "password": "changeme"}
    if csrf_token:
        data["csrf_token"] = csrf_token
    await client.post("/admin/login", data=data, follow_redirects=True)

    # 날짜 필터 POST
    stats_page = await client.get("/admin/message-statistics", follow_redirects=True)
    csrf_token = extract_csrf_token(stats_page.text) or ""

    response = await client.post(
        "/admin/message-statistics",
        data={
            "csrf_token": csrf_token,
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_vllm_status_redirect(client: AsyncClient):
    """vLLM 상태 리다이렉트 테스트"""
    # 로그인
    login_page = await client.get("/admin/login")
    csrf_token = extract_csrf_token(login_page.text)
    data = {"username": "admin", "password": "changeme"}
    if csrf_token:
        data["csrf_token"] = csrf_token
    await client.post("/admin/login", data=data, follow_redirects=True)

    # vLLM 상태 페이지 접근 (리다이렉트 확인)
    response = await client.get("/admin/vllm-status", follow_redirects=False)
    assert response.status_code == 302
    # 리다이렉트 URL이 /metrics를 포함하는지 확인
    assert "/metrics" in response.headers.get("location", "")

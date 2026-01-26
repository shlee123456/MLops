"""User Admin 테스트"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from src.serve.models.user import User, UserRole
from src.serve.core.security import verify_password


@pytest.mark.asyncio
async def test_user_admin_create_with_password(client: AsyncClient, test_db):
    """Admin에서 비밀번호와 함께 User 생성"""
    # Admin 로그인
    login_response = await client.post(
        "/admin/login",
        data={"username": "admin", "password": "changeme"}
    )
    assert login_response.status_code in [302, 303]  # Redirect

    # User 생성 (비밀번호 포함)
    create_response = await client.post(
        "/admin/user/create",
        data={
            "username": "testuser",
            "password": "testpassword123",
            "role": "user",
            "is_active": "true"
        },
        follow_redirects=False
    )

    # 생성 성공 후 리다이렉트 (302 or 303)
    assert create_response.status_code in [302, 303]

    # DB에서 User 확인
    result = await test_db.execute(
        select(User).where(User.username == "testuser")
    )
    user = result.scalar_one_or_none()

    assert user is not None
    assert user.username == "testuser"
    assert user.role == UserRole.USER
    assert user.is_active is True
    assert user.password_hash is not None
    assert verify_password("testpassword123", user.password_hash)


@pytest.mark.asyncio
async def test_user_admin_create_without_password(client: AsyncClient):
    """Admin에서 비밀번호 없이 User 생성 시도 (실패해야 함)"""
    # Admin 로그인
    login_response = await client.post(
        "/admin/login",
        data={"username": "admin", "password": "changeme"}
    )
    assert login_response.status_code in [302, 303]

    # User 생성 (비밀번호 없음)
    create_response = await client.post(
        "/admin/user/create",
        data={
            "username": "testuser2",
            "role": "user",
            "is_active": "true"
        },
        follow_redirects=False
    )

    # 폼 검증 실패 (400) 또는 페이지 재표시 (200)
    assert create_response.status_code in [200, 400]

    # 에러 메시지 확인
    assert "필수" in create_response.text or "required" in create_response.text.lower()


@pytest.mark.asyncio
async def test_user_admin_update_with_password(client: AsyncClient, test_db):
    """Admin에서 User 수정 (비밀번호 변경)"""
    # 테스트 User 생성
    from src.serve.core.security import hash_password
    user = User(
        username="updatetest",
        password_hash=hash_password("oldpassword"),
        role=UserRole.USER,
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    # Admin 로그인
    await client.post(
        "/admin/login",
        data={"username": "admin", "password": "changeme"}
    )

    # User 수정 (새 비밀번호)
    update_response = await client.post(
        f"/admin/user/edit/{user.id}",
        data={
            "username": "updatetest",
            "password": "newpassword123",
            "role": "user",
            "is_active": "true"
        },
        follow_redirects=False
    )

    assert update_response.status_code in [302, 303]

    # DB에서 확인
    await test_db.refresh(user)
    assert verify_password("newpassword123", user.password_hash)
    assert not verify_password("oldpassword", user.password_hash)


@pytest.mark.asyncio
async def test_user_admin_update_without_password(client: AsyncClient, test_db):
    """Admin에서 User 수정 (비밀번호 변경 안 함)"""
    # 테스트 User 생성
    from src.serve.core.security import hash_password
    original_hash = hash_password("keepthispassword")
    user = User(
        username="keeptest",
        password_hash=original_hash,
        role=UserRole.USER,
        is_active=True
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    # Admin 로그인
    await client.post(
        "/admin/login",
        data={"username": "admin", "password": "changeme"}
    )

    # User 수정 (비밀번호 필드 비움)
    update_response = await client.post(
        f"/admin/user/edit/{user.id}",
        data={
            "username": "keeptest",
            "role": "admin",  # role만 변경
            "is_active": "true"
        },
        follow_redirects=False
    )

    assert update_response.status_code in [302, 303]

    # DB에서 확인
    await test_db.refresh(user)
    assert user.role == UserRole.ADMIN  # role은 변경됨
    assert user.password_hash == original_hash  # 비밀번호는 유지
    assert verify_password("keepthispassword", user.password_hash)


@pytest.mark.asyncio
async def test_user_admin_role_dropdown(client: AsyncClient, test_db):
    """Admin에서 User 생성 시 role 드롭다운 선택"""
    # Admin 로그인
    await client.post(
        "/admin/login",
        data={"username": "admin", "password": "changeme"}
    )

    # User 생성 (role을 guest로 설정)
    create_response = await client.post(
        "/admin/user/create",
        data={
            "username": "guestuser",
            "password": "guestpassword",
            "role": "guest",
            "is_active": "true"
        },
        follow_redirects=False
    )

    assert create_response.status_code in [302, 303]

    # DB에서 확인
    result = await test_db.execute(
        select(User).where(User.username == "guestuser")
    )
    user = result.scalar_one_or_none()

    assert user is not None
    assert user.role == UserRole.GUEST

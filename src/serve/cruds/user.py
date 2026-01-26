"""
User CRUD Operations

사용자 관련 데이터베이스 CRUD 함수
"""

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.serve.core.security import hash_password
from src.serve.models.user import User


async def create_user(
    db: AsyncSession,
    username: str,
    password: str,
    role: str = "user",
    is_active: bool = True,
) -> User:
    """사용자 생성"""
    user = User(
        username=username,
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user(
    db: AsyncSession,
    user_id: int,
) -> Optional[User]:
    """사용자 ID로 조회"""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_username(
    db: AsyncSession,
    username: str,
) -> Optional[User]:
    """사용자명으로 조회"""
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def get_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    is_active: Optional[bool] = None,
) -> Sequence[User]:
    """사용자 목록 조회"""
    query = select(User).order_by(User.created_at.desc())

    if is_active is not None:
        query = query.where(User.is_active == is_active)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def update_user(
    db: AsyncSession,
    user_id: int,
    password: Optional[str] = None,
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> Optional[User]:
    """사용자 정보 업데이트"""
    user = await get_user(db, user_id)
    if not user:
        return None

    if password is not None:
        user.password_hash = hash_password(password)
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active

    await db.flush()
    await db.refresh(user)
    return user


async def delete_user(
    db: AsyncSession,
    user_id: int,
) -> bool:
    """사용자 삭제"""
    user = await get_user(db, user_id)
    if user:
        await db.delete(user)
        return True
    return False

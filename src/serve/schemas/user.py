"""
User Schemas

사용자 관련 Pydantic 스키마
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from src.serve.models.user import UserRole


class UserCreate(BaseModel):
    """사용자 생성 요청"""
    username: str = Field(..., min_length=3, max_length=100, description="사용자명")
    password: str = Field(..., min_length=8, description="비밀번호")
    role: UserRole = Field(default=UserRole.USER, description="역할")
    is_active: bool = Field(default=True, description="활성 상태")


class UserUpdate(BaseModel):
    """사용자 수정 요청 (부분 업데이트)"""
    password: Optional[str] = Field(None, min_length=8, description="비밀번호")
    role: Optional[UserRole] = Field(None, description="역할")
    is_active: Optional[bool] = Field(None, description="활성 상태")


class UserResponse(BaseModel):
    """사용자 응답"""
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

"""
Admin Authentication Backend - JWT 기반 인증
"""

from datetime import datetime, timedelta
from typing import Optional, Union

from jose import JWTError, jwt
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

from src.serve.core.config import settings


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.admin_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> Optional[str]:
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload.get("sub")
    except JWTError:
        return None


class AdminAuthBackend(AuthenticationBackend):
    """SQLAdmin 인증 백엔드"""

    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form.get("username"), form.get("password")
        if username == settings.admin_username and password == settings.admin_password:
            request.session.update({"token": create_access_token(data={"sub": username})})
            return True
        return False

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> RedirectResponse | bool:
        token = request.session.get("token")
        if not token or not verify_token(token):
            return RedirectResponse(request.url_for("admin:login"), status_code=302)
        return True

"""
Admin Module - SQLAdmin 관리자 인터페이스
"""

from pathlib import Path

from sqladmin import Admin

from src.serve.database import sync_engine
from src.serve.admin.auth import AdminAuthBackend
from src.serve.admin.views import (
    UserAdmin,
    LLMModelAdmin,
    LLMConfigAdmin,
    ConversationAdmin,
    ChatMessageAdmin,
    FewshotMessageAdmin,
    SystemStatusView,
    MessageStatisticsView,
    VLLMStatusView,
)
from src.serve.core.config import settings

# 템플릿 디렉토리 경로
TEMPLATES_DIR = Path(__file__).parent / "templates"


def create_admin(app) -> Admin:
    """SQLAdmin 인스턴스 생성"""
    authentication_backend = AdminAuthBackend(secret_key=settings.jwt_secret_key)
    admin = Admin(
        app,
        sync_engine,
        authentication_backend=authentication_backend,
        title="MLOps Admin",
        base_url="/admin",
        templates_dir=str(TEMPLATES_DIR),
    )

    # ModelView 등록
    admin.add_view(UserAdmin)
    admin.add_view(LLMModelAdmin)
    admin.add_view(LLMConfigAdmin)
    admin.add_view(ConversationAdmin)
    admin.add_view(ChatMessageAdmin)
    admin.add_view(FewshotMessageAdmin)

    # BaseView (커스텀 대시보드) 등록
    admin.add_view(SystemStatusView)
    admin.add_view(MessageStatisticsView)
    admin.add_view(VLLMStatusView)

    return admin


__all__ = ["create_admin"]

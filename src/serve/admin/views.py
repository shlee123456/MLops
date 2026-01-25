"""
Admin Views - SQLAdmin 모델 뷰 및 커스텀 대시보드
"""

from datetime import datetime, timedelta
from pathlib import Path

import psutil
from sqlalchemy import or_, func, cast, Date
from sqladmin import ModelView, BaseView, expose
from starlette.requests import Request
from starlette.responses import RedirectResponse
from wtforms import PasswordField, SelectField
from wtforms.validators import Optional

from src.serve.models.chat import LLMConfig, Conversation, ChatMessage, FewshotMessage
from src.serve.models.llm import LLMModel
from src.serve.models.user import User, UserRole
from src.serve.database import sync_engine
from src.serve.core.config import settings
from src.serve.core.security import hash_password


# ============================================================
# ModelView Classes
# ============================================================

class UserAdmin(ModelView, model=User):
    name = "사용자"
    name_plural = "사용자 목록"
    icon = "fa-solid fa-users"
    column_list = [User.id, User.username, User.role, User.is_active, User.created_at, User.updated_at]
    column_searchable_list = [User.username]
    column_default_sort = ("created_at", True)
    form_excluded_columns = [User.password_hash, User.created_at, User.updated_at]

    # 비밀번호 필드 추가 (가상 필드)
    form_extra_fields = {
        "password": PasswordField("비밀번호", validators=[Optional()])
    }

    # Role 필드를 SelectField로 오버라이드
    form_overrides = {
        "role": SelectField
    }

    # Role 선택지 및 기본값 설정
    form_args = {
        "role": {
            "label": "역할",
            "choices": [(role.value, role.value) for role in UserRole],
            "default": UserRole.USER.value
        }
    }

    async def insert_model(self, request: Request, data: dict) -> User:
        """Create new user with password"""
        # Form 데이터 직접 읽기
        form_data = await request.form()
        password = form_data.get("password", "")

        if not password:
            raise ValueError("비밀번호는 필수입니다")

        # password_hash 설정
        data["password_hash"] = hash_password(password)
        # password 필드가 data에 있으면 제거
        data.pop("password", None)

        return await super().insert_model(request, data)

    async def update_model(self, request: Request, pk: str, data: dict) -> User:
        """Update user, only change password if provided"""
        # Form 데이터 직접 읽기
        form_data = await request.form()
        password = form_data.get("password", "")

        # 비밀번호가 입력된 경우에만 해싱하여 저장
        if password:
            data["password_hash"] = hash_password(password)

        # password 필드가 data에 있으면 제거
        data.pop("password", None)

        return await super().update_model(request, pk, data)


class LLMModelAdmin(ModelView, model=LLMModel):
    name = "LLM 모델"
    name_plural = "LLM 모델 목록"
    icon = "fa-solid fa-cube"
    column_list = [LLMModel.id, LLMModel.name, LLMModel.api_url, LLMModel.max_tokens_limit, LLMModel.is_active, LLMModel.created_at]
    column_searchable_list = [LLMModel.name, LLMModel.api_url]
    column_default_sort = ("created_at", True)
    column_formatters = {
        LLMModel.api_url: lambda m, a: (m.api_url[:50] + "..." if m.api_url and len(m.api_url) > 50 else m.api_url),
    }

    # 필드 가이드 및 기본값 설정
    form_args = {
        "api_key": {
            "label": "API Key (저장 시 마스킹 표시)"
        },
        "api_url": {
            "label": "API URL",
            "description": "vLLM OpenAI 호환 엔드포인트 URL",
            "render_kw": {"placeholder": "http://localhost:8000/v1"}
        },
        "max_tokens_limit": {
            "label": "최대 토큰 수",
            "description": "이 모델이 생성할 수 있는 최대 토큰 수",
            "default": 2048
        }
    }


class LLMConfigAdmin(ModelView, model=LLMConfig):
    name = "LLM 설정"
    name_plural = "LLM 설정 목록"
    icon = "fa-solid fa-sliders"
    column_list = [LLMConfig.id, LLMConfig.name, LLMConfig.model_name, LLMConfig.temperature, LLMConfig.is_default, LLMConfig.created_at]
    column_searchable_list = [LLMConfig.name, LLMConfig.model_name]
    column_default_sort = ("created_at", True)


class ConversationAdmin(ModelView, model=Conversation):
    name = "대화"
    name_plural = "대화 목록"
    icon = "fa-solid fa-comments"
    column_list = [Conversation.id, Conversation.title, Conversation.session_id, Conversation.created_at, Conversation.updated_at]
    column_searchable_list = [Conversation.title, Conversation.session_id]
    column_default_sort = ("updated_at", True)
    can_delete = True

    def search_query(self, stmt, term: str):
        """커스텀 검색 - ID 숫자 검색 및 ilike 패턴 지원"""
        if term == "":
            return stmt

        # ID 숫자 검색 시도
        try:
            conv_id = int(term)
            id_filter = Conversation.id == conv_id
        except ValueError:
            id_filter = False

        return stmt.filter(
            or_(
                id_filter,
                Conversation.title.ilike(f'%{term}%'),
                Conversation.session_id.ilike(f'%{term}%')
            )
        )


class ChatMessageAdmin(ModelView, model=ChatMessage):
    name = "메시지"
    name_plural = "메시지 목록"
    icon = "fa-solid fa-message"
    column_list = [ChatMessage.id, ChatMessage.conversation_id, ChatMessage.role, ChatMessage.content, ChatMessage.created_at]
    column_searchable_list = [ChatMessage.content, ChatMessage.role]
    column_default_sort = ("created_at", True)
    can_create = False
    can_edit = False
    can_delete = False
    column_formatters = {
        ChatMessage.content: lambda m, a: (m.content[:50] + "..." if m.content and len(m.content) > 50 else m.content),
    }

    def search_query(self, stmt, term: str):
        """커스텀 검색 - ID/conversation_id 숫자 검색 및 텍스트 검색"""
        if term == "":
            return stmt

        # ID 숫자 검색 시도
        try:
            msg_id = int(term)
            id_filter = or_(
                ChatMessage.id == msg_id,
                ChatMessage.conversation_id == msg_id
            )
        except ValueError:
            id_filter = False

        return stmt.filter(
            or_(
                id_filter,
                ChatMessage.content.ilike(f'%{term}%'),
                ChatMessage.role.ilike(f'%{term}%')
            )
        )


class FewshotMessageAdmin(ModelView, model=FewshotMessage):
    name = "Few-shot 메시지"
    name_plural = "Few-shot 메시지 목록"
    icon = "fa-solid fa-list-ol"
    column_list = [
        FewshotMessage.id,
        FewshotMessage.llm_config_id,
        FewshotMessage.role,
        FewshotMessage.content,
        FewshotMessage.order,
        FewshotMessage.created_at
    ]
    column_searchable_list = [FewshotMessage.role, FewshotMessage.content]
    column_default_sort = [("llm_config_id", False), ("order", False)]
    column_formatters = {
        FewshotMessage.content: lambda m, a: (m.content[:50] + "..." if m.content and len(m.content) > 50 else m.content),
    }

    def search_query(self, stmt, term: str):
        """커스텀 검색 - llm_config_id 숫자 검색 및 텍스트 검색"""
        if term == "":
            return stmt

        # ID 숫자 검색 시도
        try:
            config_id = int(term)
            id_filter = or_(
                FewshotMessage.id == config_id,
                FewshotMessage.llm_config_id == config_id
            )
        except ValueError:
            id_filter = False

        return stmt.filter(
            or_(
                id_filter,
                FewshotMessage.role.ilike(f'%{term}%'),
                FewshotMessage.content.ilike(f'%{term}%')
            )
        )


# ============================================================
# BaseView Classes (Custom Dashboards)
# ============================================================

class SystemStatusView(BaseView):
    """시스템 상태 모니터링 대시보드"""
    name = "시스템 상태"
    icon = "fa-solid fa-server"

    @expose("/system-status", methods=["GET"])
    async def system_status_page(self, request: Request):
        # 메모리 정보
        memory = psutil.virtual_memory()

        # CPU 정보
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()

        # 디스크 정보
        disk = psutil.disk_usage('/')

        # 프로세스 정보
        process = psutil.Process()
        process_info = {
            "pid": process.pid,
            "memory_mb": process.memory_info().rss / (1024 * 1024),
            "num_threads": process.num_threads(),
        }

        # DB 연결 풀 정보
        pool = sync_engine.pool
        db_pool = {
            "Pool Class": pool.__class__.__name__,
            "Pool Size": getattr(pool, 'size', 'N/A'),
            "Checked In": pool.checkedin(),
            "Checked Out": pool.checkedout(),
            "Overflow": pool.overflow(),
            "Invalid": pool.invalidatedcount() if hasattr(pool, 'invalidatedcount') else 'N/A',
        }

        return await self.templates.TemplateResponse(
            request,
            "system_status.html",
            context={
                "memory": memory,
                "cpu_percent": cpu_percent,
                "cpu_count": cpu_count,
                "disk": disk,
                "db_pool": db_pool,
                "process_info": process_info,
            },
        )


class MessageStatisticsView(BaseView):
    """메시지 통계 대시보드"""
    name = "메시지 통계"
    icon = "fa-solid fa-chart-line"

    @expose("/message-statistics", methods=["GET", "POST"])
    async def message_statistics_page(self, request: Request):
        from sqlalchemy.orm import Session

        # 날짜 범위 기본값 (최근 30일)
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)

        # POST 요청 시 날짜 파싱
        if request.method == "POST":
            form = await request.form()
            if form.get("start_date"):
                start_date = datetime.strptime(form["start_date"], "%Y-%m-%d").date()
            if form.get("end_date"):
                end_date = datetime.strptime(form["end_date"], "%Y-%m-%d").date()

        # 쿼리 실행
        with Session(sync_engine) as session:
            # 기본 필터
            date_filter = ChatMessage.created_at.between(
                datetime.combine(start_date, datetime.min.time()),
                datetime.combine(end_date, datetime.max.time())
            )

            # 총 메시지 수
            total_messages = session.query(func.count(ChatMessage.id)).filter(date_filter).scalar() or 0

            # 총 대화 수
            total_conversations = session.query(func.count(func.distinct(ChatMessage.conversation_id))).filter(date_filter).scalar() or 0

            # 전체 평균 통계
            avg_latency_ms = session.query(func.avg(ChatMessage.latency_ms)).filter(
                date_filter,
                ChatMessage.latency_ms.isnot(None)
            ).scalar() or 0

            avg_tokens = session.query(func.avg(ChatMessage.tokens_used)).filter(
                date_filter,
                ChatMessage.tokens_used.isnot(None)
            ).scalar() or 0

            # 평균 TTFT 계산 (first_token_at - created_at 밀리초)
            # SQLite에서 datetime 차이 계산
            avg_ttft_ms = session.query(
                func.avg(
                    (func.julianday(ChatMessage.first_token_at) - func.julianday(ChatMessage.created_at)) * 86400000
                )
            ).filter(
                date_filter,
                ChatMessage.first_token_at.isnot(None)
            ).scalar() or 0

            # 역할별 통계 (TTFT 포함)
            role_stats_query = session.query(
                ChatMessage.role,
                func.count(ChatMessage.id).label('count'),
                func.avg(ChatMessage.latency_ms).label('avg_latency'),
                func.avg(ChatMessage.tokens_used).label('avg_tokens'),
                func.sum(ChatMessage.tokens_used).label('total_tokens'),
                func.avg(
                    (func.julianday(ChatMessage.first_token_at) - func.julianday(ChatMessage.created_at)) * 86400000
                ).label('avg_ttft')
            ).filter(date_filter).group_by(ChatMessage.role).all()

            role_stats = [
                {
                    "role": r.role,
                    "count": r.count,
                    "avg_latency": r.avg_latency,
                    "avg_tokens": r.avg_tokens,
                    "total_tokens": r.total_tokens,
                    "avg_ttft": r.avg_ttft,
                }
                for r in role_stats_query
            ]

            # 일별 통계 (TTFT 포함)
            daily_stats_query = session.query(
                cast(ChatMessage.created_at, Date).label('date'),
                func.count(ChatMessage.id).label('count'),
                func.avg(ChatMessage.latency_ms).label('avg_latency'),
                func.avg(ChatMessage.tokens_used).label('avg_tokens'),
                func.avg(
                    (func.julianday(ChatMessage.first_token_at) - func.julianday(ChatMessage.created_at)) * 86400000
                ).label('avg_ttft')
            ).filter(date_filter).group_by(
                cast(ChatMessage.created_at, Date)
            ).order_by(cast(ChatMessage.created_at, Date).desc()).limit(14).all()

            daily_stats = [
                {
                    "date": d.date,
                    "count": d.count,
                    "avg_latency": d.avg_latency,
                    "avg_tokens": d.avg_tokens,
                    "avg_ttft": d.avg_ttft,
                }
                for d in daily_stats_query
            ]

        # CSRF 토큰
        csrf_token = request.session.get("csrf_token", "")

        return await self.templates.TemplateResponse(
            request,
            "message_statistics.html",
            context={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_messages": total_messages,
                "total_conversations": total_conversations,
                "avg_latency_ms": avg_latency_ms,
                "avg_tokens": avg_tokens,
                "avg_ttft_ms": avg_ttft_ms,
                "role_stats": role_stats,
                "daily_stats": daily_stats,
                "csrf_token": csrf_token,
            },
        )


class VLLMStatusView(BaseView):
    """vLLM 서버 상태 리다이렉트"""
    name = "vLLM 상태"
    icon = "fa-solid fa-robot"

    @expose("/vllm-status", methods=["GET"])
    def vllm_status_page(self, request: Request):
        # vLLM /metrics 엔드포인트로 리다이렉트
        vllm_metrics_url = settings.vllm_base_url.replace("/v1", "/metrics")
        return RedirectResponse(url=vllm_metrics_url, status_code=302)

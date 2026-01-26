# admin/ - SQLAdmin 관리자 인터페이스

> **상위 문서**: [src/serve/CLAUDE.md](../CLAUDE.md) 참조

## 구조

```
admin/
├── __init__.py      # Admin 앱 생성 및 뷰 등록
├── auth.py          # JWT 인증 백엔드
├── views.py         # ModelView 및 BaseView 정의
└── templates/       # 커스텀 HTML 템플릿
    ├── system_status.html
    └── message_statistics.html
```

| 파일 | 설명 |
|------|------|
| `__init__.py` | Admin 앱 생성, templates_dir 설정 |
| `auth.py` | JWT 인증 백엔드 |
| `views.py` | ModelView (3개) + BaseView (3개) |
| `templates/` | 커스텀 대시보드 템플릿 |

## 기능

### ModelView (데이터 CRUD)

| 클래스 | 모델 | 기능 |
|--------|------|------|
| `UserAdmin` | User | 사용자 관리 + 가상 password 필드 |
| `LLMModelAdmin` | LLMModel | LLM 모델 관리 |
| `LLMConfigAdmin` | LLMConfig | LLM 설정 관리 |
| `ConversationAdmin` | Conversation | 대화 관리 + 커스텀 검색 |
| `ChatMessageAdmin` | ChatMessage | 메시지 조회 (읽기 전용) + 커스텀 검색 |
| `FewshotMessageAdmin` | FewshotMessage | Few-shot 메시지 관리 |

### 가상 필드 추가 패턴 (Virtual Fields)

**문제**: SQLAdmin 0.22.0에서 `form_extra_fields`는 구현되지 않음

**해결**: `scaffold_form()` 메서드 오버라이드

```python
from wtforms import PasswordField
from wtforms.validators import Optional

class UserAdmin(ModelView, model=User):
    # password_hash는 폼에서 제외
    form_excluded_columns = [User.password_hash, User.created_at, User.updated_at]

    async def scaffold_form(self, rules=None):
        """폼 생성 오버라이드 - password 필드 수동 추가"""
        # 기본 폼 생성
        form_class = await super().scaffold_form(rules)

        # 가상 필드 추가
        form_class.password = PasswordField("비밀번호", validators=[Optional()])

        return form_class

    async def insert_model(self, request, data):
        """Create 시 password 처리"""
        form_data = await request.form()
        password = form_data.get("password", "")
        if not password:
            raise ValueError("비밀번호는 필수입니다")
        data["password_hash"] = hash_password(password)
        data.pop("password", None)
        return await super().insert_model(request, data)

    async def update_model(self, request, pk, data):
        """Update 시 password 처리 (선택적)"""
        form_data = await request.form()
        password = form_data.get("password", "")
        if password:
            data["password_hash"] = hash_password(password)
        data.pop("password", None)
        return await super().update_model(request, pk, data)
```

**주의사항**:
- `scaffold_form(self, rules=None)` 시그니처 필수 (rules 파라미터)
- `super().scaffold_form(rules)` 호출 필수 (부모 메서드에 rules 전달)
- 가상 필드는 `insert_model`/`update_model`에서 실제 모델 필드로 변환 필요
- `form_extra_fields`는 사용하지 말 것 (미구현 기능)

### 커스텀 검색 (search_query)

- **ConversationAdmin**: ID 숫자 검색, title/session_id ilike 검색
- **ChatMessageAdmin**: ID/conversation_id 숫자 검색, content/role ilike 검색
- **FewshotMessageAdmin**: ID/llm_config_id 숫자 검색, role/content ilike 검색

### BaseView (커스텀 대시보드)

| 클래스 | 경로 | 설명 |
|--------|------|------|
| `SystemStatusView` | `/admin/system-status` | 시스템 상태 (메모리, CPU, 디스크, DB 풀) |
| `MessageStatisticsView` | `/admin/message-statistics` | 메시지 통계 (날짜 필터, 역할별/일별 통계) |
| `VLLMStatusView` | `/admin/vllm-status` | vLLM /metrics 리다이렉트 |

## 접근

- URL: `/admin`
- 로그인: `/admin/login`
- 인증: `ADMIN_USERNAME` / `ADMIN_PASSWORD`

## 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `ADMIN_USERNAME` | admin | 관리자 ID |
| `ADMIN_PASSWORD` | changeme | 관리자 비밀번호 |
| `JWT_SECRET_KEY` | change-this-... | JWT 서명 키 |
| `JWT_ALGORITHM` | HS256 | JWT 알고리즘 |
| `ADMIN_TOKEN_EXPIRE_MINUTES` | 60 | 토큰 만료 시간 |

## 의존성

- `sqladmin>=0.16.0` - Admin UI 프레임워크
- `python-jose[cryptography]>=3.3.0` - JWT 처리
- `passlib[bcrypt]>=1.7.4` - 비밀번호 해싱
- `psutil>=5.9.0` - 시스템 모니터링

## 테스트

```bash
# Admin 기능 전체
python -m pytest tests/serve/test_admin.py -v

# User Admin (password 필드 포함)
python -m pytest tests/serve/test_user_admin.py -v
```

### 테스트 항목

**test_admin.py (16개)**:
- JWT 토큰 생성/검증 (4개)
- Admin 페이지 접근 (5개)
- 커스텀 검색 (3개)
- BaseView 대시보드 (4개)

**test_user_admin.py (5개)**:
- User 생성 (비밀번호 포함/미포함)
- User 수정 (비밀번호 변경/유지)
- Role 드롭다운 선택

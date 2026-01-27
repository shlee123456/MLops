# src/serve/ - 서빙 파이프라인

> **상위 문서**: [루트 CLAUDE.md](../../CLAUDE.md) 참조

vLLM 기반 고성능 추론 + FastAPI 클린 아키텍처

## 서브 CLAUDE.md

| 경로 | 설명 |
|------|------|
| [admin/CLAUDE.md](admin/CLAUDE.md) | SQLAdmin 관리자 인터페이스 |
| [migrations/CLAUDE.md](migrations/CLAUDE.md) | Alembic DB 마이그레이션 |

## 아키텍처 구조

```
src/serve/
├── main.py              # FastAPI 엔트리포인트
├── database.py          # SQLAlchemy 비동기/동기 엔진
├── admin/               # SQLAdmin 관리자 인터페이스
│   ├── __init__.py      # Admin 앱 생성
│   ├── auth.py          # JWT 인증 백엔드
│   └── views.py         # 모델 Admin 뷰
├── core/
│   ├── config.py        # pydantic-settings 환경설정
│   └── llm.py           # vLLM 클라이언트 래퍼
├── models/
│   └── chat.py          # ORM 모델 (Conversation, ChatMessage, LLMConfig)
├── schemas/
│   └── chat.py          # Pydantic 스키마
├── cruds/
│   └── chat.py          # CRUD 함수
├── routers/
│   ├── router.py        # 라우터 통합
│   ├── chat.py          # 채팅 API 엔드포인트
│   └── dependency.py    # 의존성 주입
└── migrations/          # Alembic 마이그레이션
```

## 실행 방법

```bash
# 클린 아키텍처 서버 (권장)
python -m src.serve.main    # :8080

# 또는 vLLM 서버 직접 실행
python src/serve/01_vllm_server.py  # :8000
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 서버 정보 |
| GET | `/health` | 헬스 체크 |
| GET | `/v1/models` | 모델 목록 |
| POST | `/v1/chat/completions` | 채팅 완성 (OpenAI 호환) |
| GET | `/v1/conversations` | 대화 목록 |
| POST | `/v1/conversations` | 대화 생성 |
| GET | `/v1/conversations/{id}` | 대화 상세 |
| DELETE | `/v1/conversations/{id}` | 대화 삭제 |
| GET | `/v1/llm-configs` | LLM 설정 목록 |
| POST | `/v1/llm-configs` | LLM 설정 생성 |

## 레거시 파일 (참조용)

| 파일 | 설명 |
|------|------|
| `01_vllm_server.py` | vLLM OpenAI 호환 서버 |
| `02_vllm_client.py` | VLLMClient 클래스 (동기) |
| `03_gradio_vllm_demo.py` | Gradio UI |
| `04_fastapi_server.py` | FastAPI 레거시 (단일 파일) |
| `05_prompt_templates.py` | 프롬프트 템플릿 |
| `06_benchmark_vllm.py` | 벤치마크 |
| `07_langchain_pipeline.py` | LangChain 통합 |

## 환경설정 (core/config.py)

```python
from src.serve.core.config import settings

settings.vllm_base_url      # vLLM 서버 URL
settings.database_url       # DB 연결 문자열
settings.enable_auth        # 인증 활성화 여부
settings.api_key            # API 키
settings.default_temperature  # 기본 온도
```

## LLM 클라이언트 (core/llm.py)

```python
from src.serve.core.llm import LLMClient

client = LLMClient()

# 채팅 완성
response = await client.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7,
)

# 스트리밍
async for chunk in client.chat_completion_stream(messages):
    print(chunk)

# 종료 시
await client.close()
```

## 의존성 주입 (routers/dependency.py)

```python
from src.serve.routers.dependency import get_db, get_llm_client, verify_api_key

@router.post("/chat")
async def chat(
    db: AsyncSession = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
    _: bool = Depends(verify_api_key),
):
    ...
```

## 로깅 시스템 (core/logging.py)

FastAPI 서비스는 구조화된 JSON 로깅을 사용합니다.

### 로그 설정

**로그 위치**: `logs/fastapi/app.log` (환경변수 `LOG_DIR` 기준)

**필수 환경변수**:
```bash
LOG_DIR=/logs  # Docker 컨테이너 내부 경로
```

**로그 포맷**: JSON (structlog 기반)

**주요 필드**:
- `timestamp`: ISO 8601 형식
- `level`: INFO, WARNING, ERROR
- `request_id`: UUID (요청 추적용)
- `method`: HTTP 메서드
- `path`: 요청 경로
- `status_code`: HTTP 상태 코드
- `duration_ms`: 처리 시간 (밀리초)

### 로깅 미들웨어

`RequestLoggingMiddleware`가 모든 HTTP 요청을 자동 로깅합니다:
- `/health`, `/metrics` 경로는 제외
- 요청 시작/종료 시점 자동 기록
- 에러 발생 시 스택 트레이스 포함

### 로그 확인

```bash
# 실시간 로그 스트림
tail -f logs/fastapi/app.log | jq .

# 특정 request_id 추적
grep "request_id_value" logs/fastapi/app.log | jq .

# 에러만 필터링
jq 'select(.level=="ERROR")' logs/fastapi/app.log
```

### Docker 설정

`docker/docker-compose.serving.yml`:
```yaml
environment:
  - LOG_DIR=/logs
volumes:
  - ../logs/fastapi:/logs
```

**참고**: `docs/references/LOGGING.md` 참조

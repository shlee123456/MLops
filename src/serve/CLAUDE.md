# src/serve/ - 서빙 파이프라인

> **상위 문서**: [/CLAUDE.md](../../CLAUDE.md) - 프로젝트 전체 규칙, 환경변수, 세션 히스토리/터미널 로그 기록 방법 참조

vLLM 기반 고성능 추론 + FastAPI 래퍼 (클린 아키텍처)

## 서브 CLAUDE.md 목록

| 경로 | 설명 |
|------|------|
| [core/CLAUDE.md](core/CLAUDE.md) | 설정, vLLM 클라이언트 |
| [models/CLAUDE.md](models/CLAUDE.md) | ORM 모델 |
| [schemas/CLAUDE.md](schemas/CLAUDE.md) | Pydantic 스키마 |
| [cruds/CLAUDE.md](cruds/CLAUDE.md) | CRUD 함수 |
| [routers/CLAUDE.md](routers/CLAUDE.md) | API 라우터 |

## 디렉토리 구조

```
src/serve/
├── main.py                    # FastAPI 앱 엔트리포인트 ⭐
├── database.py                # SQLAlchemy 설정
├── core/
│   ├── config.py              # pydantic-settings
│   └── llm.py                 # vLLM 클라이언트 래퍼
├── models/
│   └── models.py              # ORM (Chat, Message, LLMConfig)
├── schemas/
│   ├── chat.py, completion.py, common.py
├── cruds/
│   └── chat.py                # CRUD 함수
├── routers/
│   ├── router.py              # 라우터 통합
│   ├── dependency.py          # 의존성 주입
│   ├── health.py, chat.py, models.py, completion.py
├── utils/
│
│── # 레거시 (참조용)
├── 01_vllm_server.py          # vLLM 서버 실행
├── 02_vllm_client.py          # VLLMClient 클래스
├── 03_gradio_vllm_demo.py     # Gradio UI
├── 04_fastapi_server.py       # 이전 단일 파일 버전
├── 05_prompt_templates.py     # 프롬프트 템플릿
├── 06_benchmark_vllm.py       # 벤치마크
└── 07_langchain_pipeline.py   # LangChain 통합
```

## 실행 방법

```bash
# 1. vLLM 서버 먼저
python src/serve/01_vllm_server.py  # :8000

# 2. FastAPI 서버 (클린 아키텍처 버전)
python -m src.serve.main  # :8080

# 또는 레거시 버전
python src/serve/04_fastapi_server.py  # :8080
```

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | API 정보 |
| GET | `/health` | 헬스 체크 |
| GET | `/metrics` | 메트릭 |
| GET | `/v1/models` | 모델 목록 |
| POST | `/v1/chat/completions` | 채팅 완성 |
| POST | `/v1/completions` | 텍스트 완성 |
| POST | `/v1/chats` | 채팅 세션 생성 |
| GET | `/v1/chats` | 채팅 목록 |
| GET | `/v1/chats/{id}` | 채팅 조회 |
| DELETE | `/v1/chats/{id}` | 채팅 삭제 |
| GET | `/v1/chats/{id}/messages` | 메시지 목록 |

## 의존성 관계

```
config.py ← database.py ← models.py ← cruds/chat.py
    ↓                         ↓
  llm.py               schemas/*.py
    ↓                         ↓
routers/*.py ← dependency.py
    ↓
  main.py
```

## 테스트

```bash
pytest tests/serve/ -v
```

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `VLLM_BASE_URL` | http://localhost:8000/v1 | vLLM 서버 |
| `FASTAPI_HOST` | 0.0.0.0 | 서버 호스트 |
| `FASTAPI_PORT` | 8080 | 서버 포트 |
| `DATABASE_URL` | sqlite+aiosqlite:///./mlops_chat.db | DB |
| `ENABLE_AUTH` | false | 인증 활성화 |
| `API_KEY` | your-secret-api-key | API 키 |

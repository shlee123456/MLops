# mlops-project 아키텍처 리팩토링 계획

> 작성일: 2026-01-15
> 참조: gmr_fastapi_server 프로젝트

## 개요

gmr_fastapi_server의 클린 아키텍처 패턴(Router/Schema/CRUD 분리)을 mlops-project에 적용합니다. 학습 단계를 고려하여 JWT 인증, SQLAdmin, 부하 테스트는 제외하고, Alembic 마이그레이션은 유지합니다.

## 현재 상태 분석

현재 `src/serve/04_fastapi_server.py`는 단일 파일에 모든 로직이 포함된 플랫 구조입니다. 이를 gmr_fastapi_server 패턴을 참고하여 계층화된 클린 아키텍처로 전환합니다.

## 목표 아키텍처

```
Client Layer
    ├── API Clients
    └── Gradio Demo
         ↓
Application Layer
    ├── main.py
    ├── routers/
    └── schemas/
         ↓
Business Layer
    └── core/
         ↓
Data Layer
    ├── models/
    ├── cruds/
    └── SQLite DB
         ↓
Infrastructure
    ├── vLLM Server
    ├── MLflow
    └── Prometheus
```

## 디렉토리 구조 변경 (간소화 버전)

```
src/serve/                          # 기존: 04_fastapi_server.py 단일 파일
├── main.py                         # FastAPI 앱 엔트리포인트
├── database.py                     # DB 연결 설정 (SQLite)
├── core/
│   ├── __init__.py
│   ├── config.py                   # pydantic-settings 환경설정
│   └── llm.py                      # vLLM 클라이언트 래퍼
├── models/
│   ├── __init__.py
│   └── models.py                   # SQLAlchemy ORM 모델 (Chat, Message, LLMConfig)
├── schemas/
│   ├── __init__.py
│   └── chat.py                     # 채팅 관련 Pydantic 스키마
├── cruds/
│   ├── __init__.py
│   └── chat.py                     # 채팅 CRUD
├── routers/
│   ├── __init__.py
│   ├── router.py                   # 라우터 집합
│   ├── chat.py                     # 채팅 API 엔드포인트
│   └── dependency.py               # 의존성 주입 (get_db, API Key 검증)
└── utils/
    └── __init__.py

db/                                 # Alembic 마이그레이션
├── alembic.ini
└── migrations/
    ├── env.py
    └── versions/
```

## 데이터베이스 스키마 (간소화 버전 - User 제외)

```
Chat
├── id (PK)
├── llm_config_id (FK)
├── session_id
└── created_at

Message
├── id (PK)
├── chat_id (FK)
├── role (enum: user/assistant/system)
├── content (text)
├── created_at
└── usage (json)

LLMConfig
├── id (PK)
├── name
├── model_name
├── system_prompt (text)
├── temperature (float)
└── max_tokens (int)
```

## TODO 목록

### Phase A: 기반 구조 (클린 아키텍처)

- [ ] 디렉토리 구조 생성 (core, models, schemas, cruds, routers, utils)
- [ ] core/config.py - pydantic-settings 환경설정 클래스 구현
- [ ] database.py - SQLAlchemy 엔진/세션 설정 (SQLite)

### Phase B: 데이터 계층

- [ ] models/models.py - Chat, Message, LLMConfig ORM 모델 (User 제외)
- [ ] Alembic 초기 설정 및 마이그레이션
- [ ] cruds/chat.py - CRUD 함수

### Phase C: 의존성 주입 (인증 제외)

- [ ] routers/dependency.py - 의존성 주입 (get_db, API Key 검증)

### Phase D: API 계층

- [ ] schemas/ - Pydantic 스키마 정의
- [ ] routers/ - API 엔드포인트 구현

### Phase E: 테스트

- [ ] 기본 기능 테스트 (test_api.py)

### Phase F: 통합 및 마무리

- [ ] main.py 리팩토링 및 통합
- [ ] 문서화 업데이트 (CLAUDE.md, API docs)

## 주요 의존성 추가

```txt
# requirements.txt 추가
sqlalchemy>=2.0
alembic>=1.13
pydantic-settings>=2.0
```

## 기존 MLOps 기능 유지

- MLflow 실험 추적: 그대로 유지
- Prometheus + Grafana + Loki: 그대로 유지
- Docker Compose 배포: 확장하여 DB 컨테이너 추가

## 제외된 항목 (프로덕션 단계에서 추가 예정)

- JWT 인증 (python-jose, passlib) - 다중 사용자 필요 시
- SQLAdmin 패널 (sqladmin) - 관리 UI 필요 시
- 부하 테스트 (locust) - 성능 검증 필요 시
- User 모델 및 역할 기반 접근제어

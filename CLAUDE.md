# MLOps Chatbot Project

LLM Fine-tuning → 프로덕션 배포 MLOps 파이프라인

## 현재 상태

- **Phase**: 2 (Fine-tuning 완료)
- **베이스 모델**: LLaMA-3-8B-Instruct
- **GPU**: RTX 5090 (31GB) + RTX 5060 Ti (15GB)
- **배포된 모델**: [2shlee/llama3-8b-ko-chat-v1](https://huggingface.co/2shlee/llama3-8b-ko-chat-v1)
- **리팩토링**: 클린 아키텍처 적용 완료 → `src/serve/CLAUDE.md`

## 기술 스택

| 분류 | 기술 |
|------|------|
| Core ML | PyTorch 2.1+, Transformers 4.35+, PEFT, bitsandbytes |
| Serving | vLLM, FastAPI, Gradio |
| MLOps | MLflow, DVC, LangChain |
| Monitoring | Prometheus, Grafana, Loki, structlog |
| DevOps | Docker, Docker Compose |
| Database | SQLAlchemy 2.0+, Alembic (마이그레이션), SQLite |
| Config | pydantic-settings |

## 서브 CLAUDE.md 목록

| 경로 | 설명 |
|------|------|
| [src/serve/CLAUDE.md](src/serve/CLAUDE.md) | FastAPI 서빙 (클린 아키텍처) |
| [src/train/CLAUDE.md](src/train/CLAUDE.md) | LoRA/QLoRA Fine-tuning |
| [src/data/CLAUDE.md](src/data/CLAUDE.md) | 데이터 파이프라인 |
| [src/evaluate/CLAUDE.md](src/evaluate/CLAUDE.md) | 모델 평가 |
| [src/utils/CLAUDE.md](src/utils/CLAUDE.md) | 로깅 유틸리티 |
| [deployment/CLAUDE.md](deployment/CLAUDE.md) | Docker 배포 |

## 디렉토리 구조

```
src/
├── train/       → src/train/CLAUDE.md
├── serve/       → src/serve/CLAUDE.md (클린 아키텍처 적용)
│   ├── main.py              # FastAPI 엔트리포인트
│   ├── database.py          # SQLAlchemy 설정
│   ├── migrations/          # Alembic 마이그레이션
│   ├── core/                # 설정, LLM 클라이언트
│   ├── models/              # ORM 모델
│   ├── schemas/             # Pydantic 스키마
│   ├── cruds/               # DB CRUD 함수
│   └── routers/             # API 라우터
├── data/        → src/data/CLAUDE.md
├── evaluate/    → src/evaluate/CLAUDE.md
└── utils/       → src/utils/CLAUDE.md
deployment/      → deployment/CLAUDE.md
tests/serve/          # API 테스트
docs/
├── guides/           # 참조 가이드 (LOGGING.md, VLLM.md, CLAUDE-GUIDE.md)
└── plans/            # 리팩토링 계획 문서
models/
├── base/             # HuggingFace 캐시
├── fine-tuned/       # LoRA 어댑터 저장
└── downloaded/       # HF Hub에서 다운로드한 모델
data/
├── processed/        # JSONL 형식 (no_robots: 9,499건)
└── synthetic_train.json  # MLOps/DevOps 특화 합성 데이터
results/              # 실험 결과
mlruns/               # MLflow 실험 저장소
logs/                 # 구조화된 로그 (JSON)
```

## 주요 명령어

```bash
source venv/bin/activate          # 가상환경

# GPU 및 환경 확인
python src/check_gpu.py

# 학습
python src/train/01_lora_finetune.py
python src/train/02_qlora_finetune.py
mlflow ui --port 5000

# 서빙
python src/serve/01_vllm_server.py   # vLLM :8000
python -m src.serve.main             # FastAPI :8080 (클린 아키텍처)

# 테스트
python -m pytest tests/serve/ -v

# DB 마이그레이션 (Alembic) - 프로젝트 루트에서 실행
alembic current                        # 현재 상태
alembic revision --autogenerate -m "설명"  # 마이그레이션 생성
alembic upgrade head                   # 적용

# Docker (전체 스택)
docker-compose up -d
```

## 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `HUGGINGFACE_TOKEN` | - | Gated 모델 접근 (필수) |
| `VLLM_BASE_URL` | http://localhost:8000/v1 | vLLM 서버 |
| `FASTAPI_PORT` | 8080 | FastAPI 포트 |
| `DATABASE_URL` | sqlite+aiosqlite:///./mlops_chat.db | DB |
| `ENABLE_AUTH` | false | 인증 활성화 |

환경 파일: `cp env.example .env`

## 참고 문서

- [CLAUDE.md 가이드라인](docs/guides/CLAUDE-GUIDE.md) - 문서 작성 규칙
- [로깅 가이드](docs/guides/LOGGING.md) - 구조화된 로깅
- [vLLM 가이드](docs/guides/VLLM.md) - vLLM 서빙

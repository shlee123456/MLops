# MLOps Chatbot Project

LLM Fine-tuning → 프로덕션 배포 MLOps 파이프라인

## 현재 상태

- **Phase**: 2 (Fine-tuning 진행 중)
- **베이스 모델**: LLaMA-3-8B-Instruct
- **GPU**: RTX 5090 (31GB) + RTX 5060 Ti (15GB)
- **리팩토링**: 클린 아키텍처 적용 예정 → `docs/plans/clean-architecture-refactoring.md`

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

## 디렉토리 구조

```
src/
├── train/       → src/train/CLAUDE.md
├── serve/       → src/serve/CLAUDE.md (클린 아키텍처 적용)
│   ├── main.py              # FastAPI 엔트리포인트
│   ├── database.py          # SQLAlchemy 설정
│   ├── core/                # 설정, LLM 클라이언트
│   ├── models/              # ORM 모델
│   ├── schemas/             # Pydantic 스키마
│   ├── cruds/               # DB CRUD 함수
│   └── routers/             # API 라우터
├── data/        → src/data/CLAUDE.md
├── evaluate/    → src/evaluate/CLAUDE.md
└── utils/       → src/utils/CLAUDE.md
deployment/      → deployment/CLAUDE.md
db/                   # Alembic 마이그레이션
docs/
├── guides/           # 참조 가이드 (LOGGING.md, VLLM.md)
└── plans/            # 리팩토링 계획 문서
models/base/          # HuggingFace 캐시
models/fine-tuned/    # LoRA 어댑터 저장
data/                 # 학습 데이터
results/              # 실험 결과
mlruns/               # MLflow 실험 저장소
logs/                 # 구조화된 로그 (JSON)
```

## 환경변수 (전체)

```bash
# 필수
HUGGINGFACE_TOKEN        # Gated 모델 접근

# MLflow
MLFLOW_TRACKING_URI      # MLflow 서버 (기본: ./mlruns)

# 서빙
VLLM_ENDPOINT            # vLLM 서버 (기본: http://localhost:8000)
GPU_MEMORY_UTILIZATION   # GPU 메모리 사용률 (기본: 0.9)
MAX_MODEL_LEN            # 최대 시퀀스 (기본: 4096)
MODEL_PATH               # 모델 경로
API_KEY                  # API 인증 키 (기본: your-secret-api-key)
ENABLE_AUTH              # 인증 활성화 (기본: false)

# 데이터베이스
DATABASE_URL             # DB 연결 (기본: sqlite:///./data/chat.db)

# 로깅
LOG_DIR                  # 로그 디렉토리 (기본: ./logs)
LOG_LEVEL                # 로그 레벨 (기본: INFO)
```

## 코딩 컨벤션

| 항목 | 규칙 | 예시 |
|------|------|------|
| Python | 3.10+, Black, isort | - |
| 파일명 | `{순번}_{기능}.py` | `01_lora_finetune.py` |
| 함수 | snake_case + type hints | `def load_data(path: str) -> Dataset:` |
| 클래스 | PascalCase | `TrainingLogger` |
| 상수 | UPPER_SNAKE | `LogType.TRAINING` |
| Docstring | Google 스타일 | `Args:`, `Returns:` |
| API 모델 | Pydantic + Field | `Field(..., description="설명")` |

## 주요 명령어

```bash
source venv/bin/activate          # 가상환경

# 로컬 실행
python src/check_gpu.py           # GPU 확인
python src/train/01_lora_finetune.py
python src/serve/main.py          # FastAPI 서버 (클린 아키텍처)
mlflow ui --port 5000

# DB 마이그레이션 (Alembic)
cd db
alembic revision --autogenerate -m "설명"  # 마이그레이션 생성
alembic upgrade head                        # 최신 버전 적용

# Docker (전체 스택)
docker-compose up -d
```

## 커밋 규칙

`.claude/skills.md` 참조 - 한글 커밋 메시지 사용

```
추가: 새로운 기능
수정: 기존 기능 변경
버그수정: 버그 해결
문서: 문서 작성/수정
리팩토링: 코드 구조 개선
```

## 주의사항

1. **OOM 방지**: `batch_size`, `max_length` 조절
2. **MLflow**: 학습 전 `mlflow.set_experiment()` 호출
3. **로깅**: `src/utils/logging_utils.py` 구조화 로거 사용
4. **HF 토큰**: Gated 모델 접근 시 환경변수 필수

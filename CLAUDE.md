# MLOps Chatbot Project

LLM Fine-tuning → 프로덕션 배포 MLOps 파이프라인

---

## ⚠️ 필수 실행 규칙 (모든 작업 전 확인)

### 1. Ralph 자율 에이전트 (권장)
복잡한 기능 개발 시 Ralph 워크플로우 사용:
```bash
# 1. PRD 작성 (prd 스킬 사용)
# "prd 스킬을 로드하고 [기능 설명]에 대한 PRD를 작성해줘"

# 2. PRD를 JSON으로 변환 (ralph 스킬 사용)
# "ralph 스킬을 로드하고 tasks/prd-[기능명].md를 prd.json으로 변환해줘"

# 3. Ralph 실행
./scripts/ralph/ralph.sh --tool claude [max_iterations]
```

### 2. 서브 CLAUDE.md 관리
- 새 디렉토리/모듈 생성 시 → 해당 디렉토리에 서브 CLAUDE.md 생성
- 기존 구조 변경 시 → 관련 서브 CLAUDE.md 업데이트
- Ralph 실행 시 발견한 패턴은 해당 CLAUDE.md에 추가

### 3. Git 커밋 규칙
- 커밋 메시지는 **한글**로 작성
- `Co-Authored-By` 태그 **사용 금지**
- 형식: `<type>: <한글 설명>` (feat, fix, docs, refactor, test, chore)
- Ralph 사용 시: `feat: [US-001] - 스토리 제목`

### 4. 작업 완료 체크리스트
- [ ] 테스트 통과했는가? (`python -m pytest tests/serve/ -v`)
- [ ] 서브 CLAUDE.md 업데이트 필요한가?
- [ ] Ralph 사용 시 progress.txt에 학습 내용 기록했는가?

---

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
| Serving | vLLM, FastAPI, Gradio, SQLAdmin |
| MLOps | MLflow, DVC, LangChain |
| Monitoring | Prometheus, Grafana, Alloy, Loki, structlog |
| DevOps | Docker, Docker Compose |
| Database | SQLAlchemy 2.0+, Alembic (마이그레이션), SQLite |
| Config | pydantic-settings |

## 서브 CLAUDE.md 목록

| 경로 | 설명 |
|------|------|
| [src/serve/CLAUDE.md](src/serve/CLAUDE.md) | FastAPI 서빙 (클린 아키텍처) |
| [src/serve/admin/CLAUDE.md](src/serve/admin/CLAUDE.md) | SQLAdmin 관리자 인터페이스 |
| [src/serve/migrations/CLAUDE.md](src/serve/migrations/CLAUDE.md) | Alembic 마이그레이션 |
| [src/train/CLAUDE.md](src/train/CLAUDE.md) | LoRA/QLoRA Fine-tuning |
| [src/data/CLAUDE.md](src/data/CLAUDE.md) | 데이터 파이프라인 |
| [src/evaluate/CLAUDE.md](src/evaluate/CLAUDE.md) | 모델 평가 |
| [src/utils/CLAUDE.md](src/utils/CLAUDE.md) | 로깅 유틸리티 |
| [deployment/CLAUDE.md](deployment/CLAUDE.md) | Docker 배포 |
| [ralph/CLAUDE.md](ralph/CLAUDE.md) | Ralph 범용 에이전트 지침 |
| [scripts/ralph/CLAUDE.md](scripts/ralph/CLAUDE.md) | Ralph MLOps 프로젝트 특화 지침 |

## 디렉토리 구조

```
src/
├── train/       → src/train/CLAUDE.md
├── serve/       → src/serve/CLAUDE.md (클린 아키텍처 적용)
│   ├── main.py              # FastAPI 엔트리포인트
│   ├── database.py          # SQLAlchemy 설정
│   ├── admin/               # SQLAdmin 관리자 인터페이스
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
├── mlflow/           # MLflow Dockerfile
├── serving/          # vLLM, FastAPI Dockerfile
├── monitoring/       # 모니터링 설정 파일
└── train/            # 학습용 Dockerfile
docker/               # Docker Compose 파일 (스택별 분리)
tests/serve/          # API 테스트
docs/
├── guides/           # Git 서브모듈 (CLAUDE-DOCS 저장소)
├── references/       # 참조 가이드 (LOGGING.md, VLLM.md)
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
ralph/                → ralph/CLAUDE.md (Ralph 도구 소스)
├── ralph.sh              # 메인 루프 스크립트 (원본)
├── skills/prd/SKILL.md   # PRD 생성 스킬
├── skills/ralph/SKILL.md # PRD→JSON 변환 스킬
└── flowchart/            # 워크플로우 시각화 (React)
scripts/ralph/        → scripts/ralph/CLAUDE.md (실행 환경)
├── ralph.sh              # 실행 스크립트 (복사본)
├── CLAUDE.md             # MLOps 특화 에이전트 지침
├── prd.json              # 사용자 스토리 (자동 생성)
└── progress.txt          # 학습 로그 (자동 생성)
tasks/                # PRD 문서 저장
```

## 주요 명령어

```bash
# pyenv 가상환경 (자동 활성화 - .python-version)
cd /path/to/mlops-project  # mlops-project 환경 자동 적용

# GPU 및 환경 확인
python src/check_gpu.py

# 모델 다운로드
python -m src.utils.download_model meta-llama/Llama-3.1-8B-Instruct
python -m src.utils.download_model --list  # 다운로드된 모델 목록

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
docker compose -f docker/docker-compose.yml up -d

# Docker (개별 스택)
docker compose -f docker/docker-compose.mlflow.yml up -d
docker compose -f docker/docker-compose.serving.yml up -d
docker compose -f docker/docker-compose.monitoring.yml up -d
```

## 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DEBUG` | false | 디버그 모드 |
| `FASTAPI_PORT` | 8080 | FastAPI 포트 |
| `VLLM_BASE_URL` | http://localhost:8000/v1 | vLLM 서버 |
| `DEFAULT_MODEL` | - | 기본 모델 (미설정 시 vLLM 기본값) |
| `DATABASE_URL` | sqlite+aiosqlite:///./mlops_chat.db | DB 연결 |
| `ENABLE_AUTH` | false | 인증 활성화 |
| `API_KEY` | your-secret-api-key | API 키 (인증 시) |
| `DEFAULT_TEMPERATURE` | 0.7 | LLM 온도 |
| `DEFAULT_MAX_TOKENS` | 512 | 최대 토큰 |
| `LOG_DIR` | ./logs/fastapi | 로그 디렉토리 |
| `HUGGINGFACE_TOKEN` | - | Gated 모델 접근 |
| `MODEL_CACHE_DIR` | models/downloaded | 모델 캐시 경로 |
| `OFFLINE_MODE` | false | 오프라인 모드 |
| `ADMIN_USERNAME` | admin | 관리자 ID |
| `ADMIN_PASSWORD` | changeme | 관리자 비밀번호 |
| `JWT_SECRET_KEY` | change-this-... | JWT 서명 키 |

환경 파일: `cp env.example .env`

## Ralph 자율 에이전트 워크플로우

Ralph는 PRD 기반으로 AI 코딩 도구를 반복 실행하는 자율 에이전트입니다.

### 디렉토리 구조
| 경로 | 역할 |
|------|------|
| `ralph/` | Ralph 도구 소스 (범용 지침, 스킬 정의, 플로우차트) |
| `scripts/ralph/` | 프로젝트 실행 환경 (MLOps 특화 지침, 런타임 파일) |

### 핵심 파일
| 파일 | 설명 |
|------|------|
| `ralph/skills/prd/SKILL.md` | PRD 생성 스킬 정의 |
| `ralph/skills/ralph/SKILL.md` | PRD→JSON 변환 스킬 정의 |
| `scripts/ralph/ralph.sh` | 메인 실행 스크립트 |
| `scripts/ralph/CLAUDE.md` | Claude Code 에이전트 지침 (MLOps 특화) |
| `scripts/ralph/prd.json` | 사용자 스토리 목록 (자동 생성) |
| `scripts/ralph/progress.txt` | 학습 내용 로그 (append-only) |
| `tasks/prd-*.md` | PRD 마크다운 문서 |

### 워크플로우
1. **PRD 작성**: `prd` 스킬(`ralph/skills/prd/`)로 `tasks/prd-[기능명].md` 생성
2. **JSON 변환**: `ralph` 스킬(`ralph/skills/ralph/`)로 `scripts/ralph/prd.json` 생성
3. **실행**: `./scripts/ralph/ralph.sh --tool claude 10`
4. **완료**: 모든 스토리가 `passes: true`가 되면 종료

### 스토리 크기 규칙
각 스토리는 **한 번의 컨텍스트 윈도우**에서 완료 가능해야 함:
- ✅ DB 컬럼 추가 + 마이그레이션
- ✅ API 엔드포인트 하나 추가
- ✅ 기존 페이지에 UI 컴포넌트 추가
- ❌ "전체 대시보드 구축" (너무 큼, 분할 필요)

### 디버깅
```bash
# 스토리 상태 확인
cat scripts/ralph/prd.json | jq '.userStories[] | {id, title, passes}'

# 학습 내용 확인
cat scripts/ralph/progress.txt

# 최근 커밋 확인
git log --oneline -10
```

## 참고 문서

- [CLAUDE.md 가이드라인](docs/guides/CLAUDE.md) - 문서 작성 규칙 (서브모듈)
- [로깅 가이드](docs/references/LOGGING.md) - 구조화된 로깅
- [vLLM 가이드](docs/references/VLLM.md) - vLLM 서빙

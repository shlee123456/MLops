# MLOps Chatbot Project

GPU 자원을 활용한 커스텀 챗봇 구축 프로젝트입니다. LLM Fine-tuning부터 프로덕션 배포까지 전체 MLOps 파이프라인을 구현합니다.

## 현재 상태

- **Phase**: 2 (Fine-tuning 진행 중)
- **베이스 모델**: LLaMA-3-8B-Instruct
- **GPU**: RTX 5090 (31GB) + RTX 5060 Ti (15GB)

## 프로젝트 목표

1. **LLM Fine-tuning 실무 경험**: LoRA/QLoRA를 활용한 효율적 학습
2. **고성능 서빙**: vLLM을 이용한 최적화된 추론
3. **End-to-End MLOps**: 데이터 수집 → 학습 → 배포 → 모니터링
4. **프로덕션 환경 구축**: FastAPI + Docker + CI/CD

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

## 프로젝트 구조

```
mlops-project/
├── src/
│   ├── train/              # 학습 스크립트
│   ├── serve/              # FastAPI 서빙 (클린 아키텍처)
│   │   ├── main.py         # FastAPI 엔트리포인트
│   │   ├── database.py     # SQLAlchemy 설정
│   │   ├── core/           # 설정, LLM 클라이언트
│   │   ├── models/         # ORM 모델
│   │   ├── schemas/        # Pydantic 스키마
│   │   ├── cruds/          # DB CRUD 함수
│   │   └── routers/        # API 라우터
│   ├── data/               # 데이터 파이프라인
│   ├── evaluate/           # 평가 스크립트
│   └── utils/              # 유틸리티 (로깅 등)
├── deployment/             # Docker Compose 배포
├── db/                     # Alembic 마이그레이션
├── docs/
│   ├── guides/             # 참조 가이드 (LOGGING.md, VLLM.md)
│   └── plans/              # 리팩토링 계획 문서
├── models/
│   ├── base/               # HuggingFace 캐시
│   └── fine-tuned/         # LoRA 어댑터 저장
├── data/                   # 학습 데이터
├── results/                # 실험 결과
├── mlruns/                 # MLflow 실험 저장소
├── logs/                   # 구조화된 로그 (JSON)
├── requirements.txt
└── README.md
```

## 시작하기

### 1. 환경 준비

```bash
# Python 가상환경 생성 (Python 3.10+ 필요)
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 토큰 입력
```

**주요 환경변수:**

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `HUGGINGFACE_TOKEN` | Gated 모델 접근 (필수) | - |
| `MLFLOW_TRACKING_URI` | MLflow 서버 | `./mlruns` |
| `VLLM_ENDPOINT` | vLLM 서버 | `http://localhost:8000` |
| `MODEL_PATH` | 모델 경로 | - |
| `API_KEY` | API 인증 키 | `your-secret-api-key` |
| `ENABLE_AUTH` | 인증 활성화 | `false` |
| `DATABASE_URL` | DB 연결 | `sqlite:///./data/chat.db` |
| `LOG_DIR` | 로그 디렉토리 | `./logs` |
| `LOG_LEVEL` | 로그 레벨 | `INFO` |

### 3. GPU 환경 확인

```bash
python src/check_gpu.py
```

## Phase별 가이드

### Phase 0: 환경 준비 ✅ 완료
- [x] 프로젝트 구조 생성
- [x] 가상환경 설정
- [x] requirements.txt 작성
- [x] GPU 환경 확인 스크립트
- [x] GPU 환경 검증 (RTX 5090 + RTX 5060 Ti)

### Phase 1: 베이스 챗봇 ✅ 완료
- [x] LLaMA-3-8B 모델 다운로드
- [x] 기본 LLM 로드 및 추론 테스트
- [x] Gradio UI 데모

### Phase 2: Fine-tuning 🔄 진행 중
- [x] 학습 데이터 준비 (HuggingFace no_robots: 9,499 examples)
- [x] 합성 데이터 생성 스크립트 (MLOps/DevOps 특화)
- [ ] LoRA fine-tuning (준비 완료)
- [ ] QLoRA fine-tuning (4-bit)
- [x] MLflow 실험 추적 설정

### Phase 3: 최적화
- [ ] vLLM 서빙 구축
- [ ] Prompt Engineering
- [ ] LangChain 파이프라인
- [ ] 성능 최적화

### Phase 4: 프로덕션화
- [x] FastAPI 백엔드 (클린 아키텍처 적용)
- [x] SQLAlchemy + Alembic DB 설정
- [ ] 스트리밍 응답
- [ ] Docker 컨테이너화
- [ ] 모니터링 (Prometheus + Grafana)
- [ ] CI/CD 파이프라인

## 필수 요구사항

### 하드웨어
- **GPU**: NVIDIA GPU 16GB+ VRAM (현재: RTX 5090 31GB + RTX 5060 Ti 15GB)
- **RAM**: 32GB+ 권장
- **Storage**: 50GB+ 여유 공간 (모델 저장용)

### 소프트웨어
- Python 3.10+
- CUDA 11.8+ (GPU 사용 시)
- Docker (배포 시)
- Git

### API 키 (선택)
- HuggingFace Token (Gated 모델 사용 시)
- OpenAI API Key (합성 데이터 생성 시)

## 주요 명령어

```bash
# 가상환경 활성화
source venv/bin/activate

# GPU 확인
python src/check_gpu.py

# 학습 데이터 준비
python src/data/01_load_dataset.py        # 공개 데이터셋
python src/data/02_generate_synthetic_data.py  # 합성 데이터

# Fine-tuning
python src/train/01_lora_finetune.py      # LoRA

# FastAPI 서버 실행 (클린 아키텍처)
python src/serve/main.py

# MLflow UI
mlflow ui --port 5000

# DB 마이그레이션 (Alembic)
cd db
alembic revision --autogenerate -m "설명"  # 마이그레이션 생성
alembic upgrade head                        # 최신 버전 적용

# Docker (전체 스택)
docker-compose up -d
```

## 트러블슈팅

### Out of Memory (OOM)
- Batch size 줄이기
- QLoRA 사용 (4-bit 양자화)
- Gradient checkpointing 활성화

### 느린 학습 속도
- Mixed precision (fp16/bf16) 사용
- Gradient accumulation 활용
- Flash Attention 적용

### 모델 다운로드 실패
- HuggingFace 토큰 확인
- 인터넷 연결 확인
- 캐시 디렉토리 권한 확인

## 상세 문서

- [vLLM 서버 가이드](docs/guides/VLLM.md) - vLLM 서빙 상세 가이드
- [로깅 시스템 가이드](docs/guides/LOGGING.md) - 구조화된 로깅 사용법
- [클린 아키텍처 리팩토링 계획](docs/plans/clean-architecture-refactoring.md) - 리팩토링 로드맵
- [배포 가이드](deployment/CLAUDE.md) - Docker Compose 배포

## 참고 자료

- [Transformers Documentation](https://huggingface.co/docs/transformers)
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [vLLM Documentation](https://vllm.readthedocs.io/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [LangChain Documentation](https://python.langchain.com/)

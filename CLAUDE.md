# CLAUDE.md

이 파일은 Claude AI가 이 프로젝트를 이해하기 위한 가이드입니다.

## 프로젝트 개요

GPU 자원을 활용한 커스텀 챗봇 구축 MLOps 프로젝트입니다. LLM Fine-tuning부터 프로덕션 배포까지 전체 MLOps 파이프라인을 구현합니다.

- **현재 단계**: Phase 2 (Fine-tuning) 진행 중
- **베이스 모델**: LLaMA-3-8B-Instruct
- **하드웨어**: RTX 5090 (31GB) + RTX 5060 Ti (15GB)

## 기술 스택

### Core ML/DL
- **Framework**: PyTorch >= 2.1.0, Transformers >= 4.35.0
- **Fine-tuning**: PEFT (LoRA, QLoRA), bitsandbytes (4-bit 양자화)
- **학습 최적화**: Accelerate, Gradient Checkpointing, Mixed Precision (fp16/bf16)

### Serving & API
- **추론 서버**: vLLM >= 0.2.6
- **API 서버**: FastAPI >= 0.104.0, Uvicorn
- **UI**: Gradio >= 4.7.0, Streamlit >= 1.28.0

### MLOps Tools
- **Experiment Tracking**: MLflow >= 2.9.0
- **Data Versioning**: DVC >= 3.30.0
- **Orchestration**: LangChain >= 0.1.0

### Monitoring & Logging
- **Metrics**: Prometheus, Grafana
- **Structured Logging**: structlog, python-json-logger
- **로그 수집**: Loki, Promtail

### DevOps
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions (예정)

### Code Quality
- **Formatter**: Black
- **Linter**: Flake8
- **Import Sorting**: isort
- **Type Checking**: mypy
- **Testing**: pytest, pytest-asyncio

## 프로젝트 구조

```
mlops/
├── data/                     # 데이터셋
│   ├── raw/                  # 원본 데이터
│   ├── processed/            # 전처리된 데이터 (*.jsonl)
│   └── synthetic_train.json  # 합성 학습 데이터
├── models/                   # 모델 저장소
│   ├── base/                 # HuggingFace 모델 캐시
│   └── fine-tuned/           # Fine-tuned 모델 (LoRA adapters)
├── src/                      # 소스 코드
│   ├── data/                 # 데이터 파이프라인
│   │   ├── 01_load_dataset.py
│   │   └── 02_generate_synthetic_data.py
│   ├── train/                # 학습 스크립트
│   │   ├── 01_lora_finetune.py
│   │   └── 02_qlora_finetune.py
│   ├── serve/                # 서빙 관련
│   │   ├── 01_vllm_server.py
│   │   ├── 02_vllm_client.py
│   │   ├── 04_fastapi_server.py
│   │   └── 07_langchain_pipeline.py
│   ├── evaluate/             # 평가 스크립트
│   └── utils/                # 유틸리티
│       ├── logging_utils.py  # 구조화된 로깅
│       └── gpu_monitor.py    # GPU 모니터링
├── deployment/               # 배포 관련
│   ├── docker/               # Dockerfile들
│   └── configs/              # Prometheus, Grafana 설정
├── mlruns/                   # MLflow 실험 저장소
├── logs/                     # 구조화된 로그 (JSON)
│   ├── training/
│   ├── inference/
│   ├── system/
│   └── vllm/
└── results/                  # 실험 결과
```

## 코딩 컨벤션

### Python 스타일
- **Python 버전**: 3.10+
- **Formatter**: Black (기본 설정)
- **Import 순서**: isort (표준 라이브러리 → 서드파티 → 로컬)
- **Type Hints**: 함수 시그니처에 타입 힌트 사용 권장

### 파일 네이밍
- 스크립트: `{순번}_{기능명}.py` 형식 (예: `01_lora_finetune.py`)
- 모듈: snake_case (예: `logging_utils.py`)

### 함수/클래스 네이밍
- 함수: snake_case (예: `load_training_data()`)
- 클래스: PascalCase (예: `TrainingLogger`)
- 상수: UPPER_SNAKE_CASE (예: `LogType.TRAINING`)

### Docstring
- 모듈: 파일 상단에 """Triple quotes""" 사용
- 함수: Google 스타일 docstring 권장
```python
def function_name(param: str) -> bool:
    """함수 설명

    Args:
        param: 파라미터 설명

    Returns:
        반환값 설명
    """
```

### 로깅 패턴
- 구조화된 로깅 사용 (`src/utils/logging_utils.py`)
- 로그 타입: `training`, `inference`, `system`, `api`
- JSON 포맷으로 출력 (Loki/Grafana 연동)

### Pydantic 모델
- API 요청/응답에 Pydantic BaseModel 사용
- Field에 description 포함
```python
class ChatRequest(BaseModel):
    messages: List[Message] = Field(..., description="대화 메시지 리스트")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
```

### 환경 변수
- `.env` 파일로 관리 (python-dotenv 사용)
- 주요 변수: `HUGGINGFACE_TOKEN`, `BASE_MODEL_NAME`, `MLFLOW_TRACKING_URI`

## 빌드 및 실행 명령어

```bash
# 가상환경 활성화
source venv/bin/activate

# GPU 확인
python src/check_gpu.py

# 학습 데이터 준비
python src/data/01_load_dataset.py
python src/data/02_generate_synthetic_data.py

# Fine-tuning
python src/train/01_lora_finetune.py     # LoRA
python src/train/02_qlora_finetune.py    # QLoRA (4-bit)

# MLflow UI
mlflow ui --port 5000

# vLLM 서버 실행
python src/serve/01_vllm_server.py

# FastAPI 서버 실행
python src/serve/04_fastapi_server.py

# Docker Compose (전체 스택)
docker-compose up -d
```

## 주요 컴포넌트

### 1. 학습 파이프라인 (`src/train/`)
- **LoRA/QLoRA Fine-tuning**: PEFT 라이브러리 활용
- **4-bit 양자화**: bitsandbytes BitsAndBytesConfig
- **MLflow 통합**: 자동 파라미터/메트릭 로깅
- **커스텀 콜백**: `LoggingCallback`으로 구조화된 로깅

### 2. 서빙 파이프라인 (`src/serve/`)
- **vLLM 서버**: 고성능 추론 엔진
- **FastAPI 래퍼**: 인증, 로깅, 모니터링 추가
- **OpenAI 호환 API**: `/v1/chat/completions`, `/v1/completions`
- **스트리밍 지원**: SSE (Server-Sent Events)

### 3. 로깅 시스템 (`src/utils/logging_utils.py`)
- `TrainingLogger`: 학습 메트릭 (epoch, step, loss)
- `InferenceLogger`: 추론 메트릭 (latency, tokens/sec)
- `SystemLogger`: 시스템 메트릭 (GPU, CPU, 메모리)
- `APILogger`: API 요청/응답 로깅

### 4. 모니터링 스택 (`deployment/configs/`)
- **Prometheus**: 메트릭 수집
- **Grafana**: 대시보드 시각화
- **Loki**: 로그 집계
- **Promtail**: 로그 수집 에이전트

## 개발 시 주의사항

1. **메모리 관리**: GPU OOM 방지를 위해 batch_size, max_length 조절
2. **HuggingFace 토큰**: Gated 모델 접근 시 `HUGGINGFACE_TOKEN` 환경변수 필요
3. **MLflow 실험**: 학습 전 `mlflow.set_experiment()` 호출 확인
4. **로그 디렉토리**: 기본값 `./logs`, 환경변수 `LOG_DIR`로 변경 가능

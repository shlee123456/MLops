# 프로젝트 현황 및 로드맵

작성일: 2025-12-11
최종 업데이트: 2025-12-13 (Phase 2 데이터 준비 완료)

## 프로젝트 개요

**목표:** LLM Fine-tuning + End-to-End MLOps 파이프라인 구축

**핵심 기술:**
- LLM: **LLaMA-3-8B-Instruct** (현재) / Mistral-7B / LLaMA-2-7B
- Fine-tuning: LoRA / QLoRA (PEFT)
- Serving: vLLM, FastAPI
- MLOps: MLflow, DVC, Docker
- 모니터링: Prometheus + Grafana

**현재 하드웨어:**
- GPU 0: NVIDIA RTX 5090 (31GB VRAM) - 메인 사용
- GPU 1: NVIDIA RTX 5060 Ti (15GB VRAM) - 보조
- CUDA 12.8, PyTorch 2.9.0
- Python 3.12.3

---

## 완료된 작업 ✅

### Phase 0: 프로젝트 초기화 ✅ 완료
- [x] 프로젝트 디렉토리 구조 생성
- [x] requirements.txt 작성 (모든 의존성 포함)
- [x] 환경 변수 템플릿 (.env.example)
- [x] .gitignore 설정
- [x] Git 저장소 초기화
- [x] README.md 작성
- [x] QUICKSTART.md 작성
- [x] setup.sh 자동화 스크립트
- [x] 가상환경 생성 및 패키지 설치
- [x] GPU 환경 확인 완료 (RTX 5090 + RTX 5060 Ti)
- [x] HuggingFace 토큰 설정

**핵심 파일:**
```
requirements.txt      # 전체 패키지 목록
.env.example         # 환경 변수 템플릿
setup.sh             # 자동 설치 스크립트
README.md            # 프로젝트 개요
QUICKSTART.md        # 빠른 시작 가이드
```

### Phase 1: 베이스 모델 테스트 ✅ 완료
- [x] GPU 환경 확인 스크립트 작성 (`src/check_gpu.py`)
- [x] GPU 환경 확인 실행 완료 (RTX 5090 + RTX 5060 Ti)
- [x] 기본 LLM 로드 및 추론 테스트 스크립트 작성 (`src/01_test_base_model.py`)
- [x] Gradio 인터랙티브 데모 스크립트 작성 (`src/02_gradio_demo.py`)
- [x] 성능 벤치마크 스크립트 작성 (`src/03_benchmark.py`)
- [x] 모델 선택: LLaMA-3-8B-Instruct (실습 최적화)
- [x] LLaMA-3-8B 모델 다운로드 완료
- [x] LLaMA-3-8B 추론 테스트 성공 (Full precision)
- [x] Gradio 데모 실행 성공 (http://localhost:7860)
- [x] Multi-GPU 스크립트 수정 완료
- [ ] 성능 벤치마크 실행 (선택사항)

**주요 기능:**
- Full precision / 4-bit quantization 옵션
- GPU 메모리 사용량 측정
- 실시간 채팅 인터페이스 (Gradio)
- 파라미터 조정 가능 (temperature, top-p, etc.)
- Multi-GPU 자동 분산 지원

**실행 결과:**
- 환경: RTX 5090 (31GB VRAM)
- 모델: LLaMA-3-8B-Instruct
- 로딩 방식: Full precision (FP16)
- VRAM 사용량: ~14GB
- 상태: ✅ 정상 동작 확인

**변경 사항:**
- LLaMA-3-70B → LLaMA-3-8B (메모리 효율성 및 실습 최적화)
- Gradio 최신 버전 호환성 수정

### Phase 2: Fine-tuning 🔄 데이터 준비 완료
- [x] 데이터셋 로드 스크립트 작성 (`src/data/01_load_dataset.py`)
  - 공개 데이터셋 다운로드
  - 데이터 탐색 및 분석
  - 학습용 포맷 변환
- [x] 합성 데이터 생성 스크립트 작성 (`src/data/02_generate_synthetic_data.py`)
  - MLOps/DevOps 도메인 특화 (25개 주제)
  - OpenAI API 통합 (선택)
  - 템플릿 기반 생성 (무료)
- [x] LoRA fine-tuning 스크립트 작성 (`src/train/01_lora_finetune.py`)
  - PEFT 통합
  - MLflow 실험 추적
  - Instruction-following 포맷
- [x] QLoRA fine-tuning 스크립트 작성 (`src/train/02_qlora_finetune.py`)
  - 4-bit 양자화
  - 메모리 효율적 학습
  - MLflow 통합
- [x] 학습 데이터셋 준비 완료 ✅
  - HuggingFace no_robots 데이터셋 다운로드
  - 9,499개 고품질 instruction-following examples
  - JSONL 포맷 변환 완료 (`data/processed/no_robots_train.jsonl`)
- [x] 합성 데이터 생성 실행 완료 ✅
  - 100개 MLOps/DevOps Q&A 생성
  - 템플릿 기반 생성 (`data/synthetic_train.json`)
- [ ] LoRA Fine-tuning 학습 실행 (준비 완료, 실행 대기)
- [ ] QLoRA Fine-tuning 학습 실행 (준비 완료, 실행 대기)
- [ ] MLflow 실험 추적 및 비교 분석

**주요 기능:**
- 여러 데이터셋 지원 (no_robots, Alpaca, Dolly, etc.)
- 자동 데이터 전처리 및 포맷 변환
- 하이퍼파라미터 커스터마이징
- MLflow 자동 로깅
- 학습 진행 상황 추적

**준비 완료 상태:**
- 데이터: `data/processed/no_robots_train.jsonl` (9,499 examples)
- 모델: LLaMA-3-8B-Instruct
- 환경: RTX 5090 (31GB VRAM)
- 학습 방식: LoRA (FP16) + QLoRA (4-bit)
- 실험 추적: MLflow 설정 완료

**다음 실행 단계:**
```bash
# LoRA Fine-tuning (예상 VRAM: 18-24GB)
python src/train/01_lora_finetune.py

# QLoRA Fine-tuning (예상 VRAM: 8-12GB)
python src/train/02_qlora_finetune.py

# MLflow UI
mlflow ui  # http://localhost:5000
```

---

## 작성된 스크립트 목록

### 환경 설정
```
setup.sh                          # 자동 설치
src/check_gpu.py                  # GPU 환경 확인
```

### Phase 1: 베이스 모델
```
src/01_test_base_model.py         # 모델 로드 및 추론
src/02_gradio_demo.py             # 웹 UI 데모
src/03_benchmark.py               # 성능 벤치마크
```

### Phase 2: 데이터 및 학습
```
src/data/01_load_dataset.py       # 데이터셋 로드
src/data/02_generate_synthetic_data.py  # 합성 데이터 생성
src/train/01_lora_finetune.py     # LoRA 학습
src/train/02_qlora_finetune.py    # QLoRA 학습
```

---

## 진행 중/예정 작업 🚧

### Phase 3: 최적화 (예정)

**목표:** 고성능 서빙 및 프롬프트 최적화

**작업 항목:**
- [ ] vLLM 서버 구축
  - `src/serve/01_vllm_server.py`
  - 고속 추론 서버
  - 배치 처리 최적화
- [ ] Prompt Engineering
  - `src/serve/02_prompt_templates.py`
  - 템플릿 시스템
  - Few-shot learning
- [ ] LangChain 통합
  - `src/serve/03_langchain_pipeline.py`
  - RAG (Retrieval-Augmented Generation)
  - Chain 구성
- [ ] 성능 최적화
  - 캐싱 전략
  - 요청 배칭
  - KV 캐시 최적화

**예상 소요 시간:** 5-7일

### Phase 4: 프로덕션화 (예정)

**목표:** 실전 배포 가능한 시스템 구축

**작업 항목:**
- [ ] FastAPI 백엔드
  - `src/serve/04_fastapi_server.py`
  - RESTful API
  - 스트리밍 응답
  - 인증/권한 관리
- [ ] Docker 컨테이너화
  - `deployment/docker/Dockerfile.train`
  - `deployment/docker/Dockerfile.serve`
  - `deployment/docker/docker-compose.yml`
- [ ] 모니터링 시스템
  - Prometheus 메트릭 수집
  - Grafana 대시보드
  - 알림 설정
- [ ] CI/CD 파이프라인
  - `.github/workflows/train.yml`
  - `.github/workflows/deploy.yml`
  - 자동 테스트
  - 자동 배포

**예상 소요 시간:** 5-7일

---

## 프로젝트 구조

```
mlops-project/
├── README.md                    # 프로젝트 개요
├── QUICKSTART.md                # 빠른 시작 가이드
├── PROJECT_STATUS.md            # 현재 문서
├── requirements.txt             # 패키지 목록
├── setup.sh                     # 자동 설치
├── .env.example                 # 환경 변수 템플릿
├── .gitignore                   # Git 제외 파일
│
├── data/                        # 데이터
│   ├── raw/                     # 원본 데이터
│   ├── processed/               # 전처리 데이터
│   └── synthetic_train.json     # 합성 데이터
│
├── models/                      # 모델 저장소
│   ├── base/                    # 원본 모델 (캐시)
│   └── fine-tuned/              # Fine-tuned 모델
│       ├── lora-mistral-custom/
│       └── qlora-mistral-custom/
│
├── src/                         # 소스 코드
│   ├── check_gpu.py             # ✅ GPU 확인
│   ├── 01_test_base_model.py    # ✅ 모델 테스트
│   ├── 02_gradio_demo.py        # ✅ Gradio 데모
│   ├── 03_benchmark.py          # ✅ 벤치마크
│   │
│   ├── data/                    # 데이터 파이프라인
│   │   ├── 01_load_dataset.py   # ✅ 데이터 로드
│   │   └── 02_generate_synthetic_data.py  # ✅ 합성 데이터
│   │
│   ├── train/                   # 학습
│   │   ├── 01_lora_finetune.py  # ✅ LoRA
│   │   └── 02_qlora_finetune.py # ✅ QLoRA
│   │
│   ├── serve/                   # 서빙 (예정)
│   │   ├── 01_vllm_server.py    # 🚧 vLLM
│   │   ├── 02_prompt_templates.py  # 🚧 Prompts
│   │   ├── 03_langchain_pipeline.py  # 🚧 LangChain
│   │   └── 04_fastapi_server.py    # 🚧 FastAPI
│   │
│   └── evaluate/                # 평가 (예정)
│       └── 01_model_eval.py     # 🚧 평가 스크립트
│
├── notebooks/                   # Jupyter 노트북
│   └── experiments.ipynb        # 🚧 실험 노트북
│
├── configs/                     # 설정 파일
│   └── train_config.yaml        # 🚧 학습 설정
│
├── tests/                       # 테스트
│   └── test_*.py                # 🚧 단위 테스트
│
└── deployment/                  # 배포
    ├── docker/                  # Docker
    │   ├── Dockerfile.train     # 🚧 학습용
    │   ├── Dockerfile.serve     # 🚧 서빙용
    │   └── docker-compose.yml   # 🚧 Compose
    │
    ├── k8s/                     # Kubernetes (선택)
    │   └── *.yaml               # 🚧 Manifests
    │
    └── scripts/                 # 배포 스크립트
        └── deploy.sh            # 🚧 배포 자동화

└── mlruns/                      # MLflow 실험 로그
```

**범례:**
- ✅ 완료
- 🚧 예정

---

## 다음 실행 단계

### 완료된 단계 ✅

1. **✅ 환경 설정** - 완료
   ```bash
   source venv/bin/activate
   python src/check_gpu.py
   ```

2. **✅ 베이스 모델 테스트** - 완료
   ```bash
   python src/01_test_base_model.py  # Full precision
   ```

3. **✅ Gradio 데모** - 완료
   ```bash
   python src/02_gradio_demo.py  # http://localhost:7860
   ```

### 다음 진행 단계 (Phase 2: Fine-tuning)

4. **✅ 데이터 준비** - 완료
   ```bash
   # ✅ 완료: HuggingFace no_robots 데이터셋 (9,499 examples)
   # 파일: data/processed/no_robots_train.jsonl

   # ✅ 완료: 합성 데이터 생성 (100 examples)
   # 파일: data/synthetic_train.json
   ```

5. **🔄 Fine-tuning 학습** - 다음 단계
   ```bash
   # LoRA Fine-tuning (예상 VRAM: 18-24GB)
   python src/train/01_lora_finetune.py
   # 입력: data/processed/no_robots_train.jsonl

   # QLoRA Fine-tuning (예상 VRAM: 8-12GB, 메모리 효율적)
   python src/train/02_qlora_finetune.py
   # 입력: data/processed/no_robots_train.jsonl
   ```

6. **⏳ MLflow 실험 추적 확인**
   ```bash
   mlflow ui
   # http://localhost:5000
   # LoRA vs QLoRA 성능/메모리/속도 비교
   ```

### 선택 사항

**성능 벤치마크** (Phase 1)
```bash
python src/03_benchmark.py
```

---

## 학습 포인트

이 프로젝트를 통해 습득할 수 있는 기술:

### MLOps 핵심 역량
1. **모델 개발**
   - LLM 아키텍처 이해
   - Fine-tuning 기법 (LoRA, QLoRA)
   - 하이퍼파라미터 튜닝

2. **실험 관리**
   - MLflow 실험 추적
   - 메트릭 로깅
   - 모델 버저닝

3. **데이터 파이프라인**
   - 데이터셋 큐레이션
   - 전처리 자동화
   - 합성 데이터 생성

4. **최적화**
   - 양자화 (4-bit, 8-bit)
   - 메모리 최적화
   - 추론 속도 개선

5. **배포 (예정)**
   - 서빙 인프라 (vLLM, FastAPI)
   - 컨테이너화 (Docker)
   - 모니터링 (Prometheus, Grafana)

---

## 리소스 요구사항

### 개발 환경
- **최소:** CPU, 16GB RAM, 50GB 디스크
- **권장:** GPU (4GB+ VRAM), 32GB RAM, 100GB 디스크
- **최적:** GPU (16GB+ VRAM), 64GB RAM, 200GB 디스크

### 소프트웨어
- Python 3.10+
- CUDA 11.8+ (GPU 사용 시)
- Docker (배포 시)
- Git

---

## 참고 자료

### 공식 문서
- [HuggingFace Transformers](https://huggingface.co/docs/transformers)
- [PEFT (LoRA/QLoRA)](https://huggingface.co/docs/peft)
- [MLflow](https://mlflow.org/docs/latest/)
- [vLLM](https://vllm.readthedocs.io/)

### 논문
- LoRA: [arxiv.org/abs/2106.09685](https://arxiv.org/abs/2106.09685)
- QLoRA: [arxiv.org/abs/2305.14314](https://arxiv.org/abs/2305.14314)

### 커뮤니티
- HuggingFace Discord
- MLOps Community Slack

---

## 버전 히스토리

### v0.1 (2025-12-11)
- ✅ Phase 0: 프로젝트 초기화
- ✅ Phase 1: 베이스 모델 테스트 스크립트 작성
- ✅ Phase 2: Fine-tuning 스크립트 작성
- 📝 문서 작성 (README, QUICKSTART, PROJECT_STATUS)

### v0.1.1 (2025-12-13 오전)
- ✅ GPU 환경 확인 및 검증 (RTX 5090 + RTX 5060 Ti)
- ✅ 모델 선택: LLaMA-3-8B-Instruct (실습 최적화)
- ✅ Phase 1 완료: 베이스 모델 테스트
  - LLaMA-3-8B 모델 다운로드 및 로딩 성공
  - Full precision 추론 테스트 성공
  - Gradio 웹 데모 실행 성공
  - Multi-GPU 스크립트 개선
- 📝 PROJECT_STATUS.md 업데이트

### v0.1.2 (2025-12-13 오후) - 현재
- ✅ Phase 2 데이터 준비 완료
  - HuggingFace no_robots 데이터셋 다운로드 (9,499 examples)
  - JSONL 포맷 변환 완료
  - 합성 데이터 생성 스크립트 실행 (100 examples)
  - 데이터 품질 검증 완료
- ✅ Fine-tuning 환경 설정 완료
  - LoRA 스크립트 준비 완료
  - QLoRA 스크립트 준비 완료
  - MLflow 설정 확인
- 📝 README.md 및 PROJECT_STATUS.md 업데이트

### v0.2 (진행 예정)
- 🔄 Phase 2 실행: Fine-tuning
  - LoRA 학습 실행
  - QLoRA 학습 실행
  - MLflow 실험 추적 및 비교
- 🚧 Phase 3: 최적화 (vLLM, LangChain)
- 🚧 평가 스크립트
- 🚧 Jupyter 노트북

### v1.0 (예정)
- 🚧 Phase 4: 프로덕션화
- 🚧 Docker 배포
- 🚧 모니터링 시스템
- 🚧 CI/CD 파이프라인

---

**프로젝트 진행률:** Phase 1 완료, Phase 2 데이터 준비 완료 (50% 완성)

**현재 상태:**
- ✅ Phase 0: 환경 준비 완료
- ✅ Phase 1: 베이스 모델 테스트 완료
- 🔄 Phase 2: 데이터 준비 완료, Fine-tuning 실행 대기
- ⏳ Phase 3: 최적화 대기
- ⏳ Phase 4: 프로덕션화 대기

**다음 마일스톤:** Phase 2 LoRA/QLoRA Fine-tuning 실행 및 MLflow 비교 분석

**준비 완료 데이터:**
- `data/processed/no_robots_train.jsonl` - 9,499개 고품질 examples
- `data/synthetic_train.json` - 100개 MLOps/DevOps Q&A

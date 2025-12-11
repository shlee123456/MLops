# MLOps Chatbot Project

GPU 자원을 활용한 커스텀 챗봇 구축 프로젝트입니다. LLM Fine-tuning부터 프로덕션 배포까지 전체 MLOps 파이프라인을 구현합니다.

## 프로젝트 목표

1. **LLM Fine-tuning 실무 경험**: LoRA/QLoRA를 활용한 효율적 학습
2. **고성능 서빙**: vLLM을 이용한 최적화된 추론
3. **End-to-End MLOps**: 데이터 수집 → 학습 → 배포 → 모니터링
4. **프로덕션 환경 구축**: FastAPI + Docker + CI/CD

## 기술 스택

### Core ML
- **Base Model**: Mistral-7B-Instruct / LLaMA-2-7B
- **Fine-tuning**: LoRA, QLoRA (PEFT)
- **Framework**: PyTorch, Transformers, Accelerate

### MLOps Tools
- **Experiment Tracking**: MLflow
- **Data Versioning**: DVC
- **Serving**: vLLM, FastAPI
- **Orchestration**: LangChain

### DevOps
- **Containerization**: Docker
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: GitHub Actions (예정)

## 프로젝트 구조

```
mlops-project/
├── data/                    # 데이터셋
│   ├── raw/                # 원본 데이터
│   └── processed/          # 전처리된 데이터
├── models/                  # 모델 저장소
│   ├── base/               # 사전학습 모델
│   └── fine-tuned/         # Fine-tuned 모델
├── src/
│   ├── data/               # 데이터 파이프라인
│   ├── train/              # 학습 스크립트
│   ├── serve/              # 서빙 관련
│   └── evaluate/           # 평가 스크립트
├── notebooks/              # 실험용 노트북
├── configs/                # 설정 파일
├── tests/                  # 테스트 코드
├── deployment/             # 배포 관련
│   ├── docker/
│   ├── k8s/
│   └── scripts/
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

### 3. GPU 환경 확인

```bash
python src/check_gpu.py
```

## Phase별 가이드

### Phase 0: 환경 준비 ✅
- [x] 프로젝트 구조 생성
- [x] 가상환경 설정
- [x] requirements.txt 작성
- [ ] GPU 환경 확인 스크립트

### Phase 1: 베이스 챗봇 (1-2일)
- [ ] 기본 LLM 로드 및 추론 테스트
- [ ] Gradio UI 데모
- [ ] 성능 벤치마크

### Phase 2: Fine-tuning (3-4일)
- [ ] 학습 데이터 준비
- [ ] 합성 데이터 생성 (GPT-4)
- [ ] LoRA fine-tuning
- [ ] QLoRA fine-tuning (4-bit)
- [ ] MLflow 실험 추적

### Phase 3: 최적화 (5-7일)
- [ ] vLLM 서빙 구축
- [ ] Prompt Engineering
- [ ] LangChain 파이프라인
- [ ] 성능 최적화

### Phase 4: 프로덕션화 (5-7일)
- [ ] FastAPI 백엔드
- [ ] 스트리밍 응답
- [ ] Docker 컨테이너화
- [ ] 모니터링 (Prometheus + Grafana)
- [ ] CI/CD 파이프라인

## 필수 요구사항

### 하드웨어
- **GPU**: NVIDIA GPU 16GB+ VRAM (권장: A100, A10, RTX 3090/4090)
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

# 베이스 모델 테스트
python src/01_test_base_model.py

# Gradio 데모 실행
python src/02_gradio_demo.py

# Fine-tuning
python src/train/01_lora_finetune.py

# MLflow UI
mlflow ui

# vLLM 서버 실행
python -m vllm.entrypoints.api_server \
  --model ./models/fine-tuned/lora-mistral-custom \
  --port 8000
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

## 참고 자료

- [Transformers Documentation](https://huggingface.co/docs/transformers)
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [vLLM Documentation](https://vllm.readthedocs.io/)
- [MLflow Documentation](https://mlflow.org/docs/latest/index.html)
- [LangChain Documentation](https://python.langchain.com/)

## 라이선스

MIT License

## 작성자

DevOps Engineer learning MLOps

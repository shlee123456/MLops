# vLLM 서버 구축 가이드

작성일: 2025-12-18
Phase 3: 최적화 및 서빙

---

## 목차

1. [개요](#개요)
2. [사전 요구사항](#사전-요구사항)
3. [빠른 시작](#빠른-시작)
4. [상세 가이드](#상세-가이드)
5. [고급 기능](#고급-기능)
6. [트러블슈팅](#트러블슈팅)

---

## 개요

vLLM은 고성능 LLM 추론을 위한 서빙 엔진입니다. 이 가이드는 Phase 3에서 작성된 모든 vLLM 관련 스크립트의 사용법을 설명합니다.

### 주요 기능

- ✅ OpenAI API 호환 서버
- ✅ 고속 추론 (PagedAttention)
- ✅ 배치 처리 최적화
- ✅ LoRA/QLoRA 어댑터 지원
- ✅ 스트리밍 응답
- ✅ Multi-GPU 지원

### 작성된 스크립트

```
src/serve/
├── 01_vllm_server.py           # vLLM 서버 메인
├── 02_vllm_client.py            # API 클라이언트
├── 03_gradio_vllm_demo.py       # Gradio 웹 UI
├── 04_fastapi_server.py         # FastAPI 래퍼
├── 05_prompt_templates.py       # 프롬프트 템플릿
├── 06_benchmark_vllm.py         # 성능 벤치마크
└── 07_langchain_pipeline.py     # LangChain 통합
```

---

## 사전 요구사항

### 하드웨어

- **GPU**: NVIDIA GPU (CUDA 지원)
  - 최소: 8GB VRAM (LLaMA-3-8B 4-bit)
  - 권장: 16GB+ VRAM (LLaMA-3-8B FP16)
- **RAM**: 32GB+ 권장
- **Storage**: 100GB+ (모델 저장 공간)

### 소프트웨어

```bash
# Python 3.10+
python --version

# CUDA 12.1+
nvidia-smi

# 필수 패키지
pip install vllm>=0.2.6
pip install openai>=1.0.0
pip install gradio>=4.0.0
pip install fastapi uvicorn
pip install langchain langchain-openai
```

### 환경 변수 설정

`.env` 파일에 다음을 추가:

```bash
# 모델 설정
BASE_MODEL_NAME=meta-llama/Meta-Llama-3-8B-Instruct
HF_HOME=./models/base

# vLLM 서버
VLLM_BASE_URL=http://localhost:8000/v1

# FastAPI 서버
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8080
ENABLE_AUTH=false
API_KEY=your-secret-api-key

# HuggingFace
HUGGINGFACE_TOKEN=your_hf_token_here
```

---

## 빠른 시작

### Step 1: vLLM 서버 시작 (베이스 모델)

```bash
# 터미널 1: vLLM 서버 실행
python src/serve/01_vllm_server.py

# 또는 커스텀 설정으로
python src/serve/01_vllm_server.py \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096
```

**예상 소요 시간**: 2-5분 (모델 로딩)
**메모리 사용량**: ~14GB VRAM (FP16)

### Step 2: 클라이언트 테스트

```bash
# 터미널 2: 클라이언트 테스트
python src/serve/02_vllm_client.py test
```

**출력 예시**:
```
✓ Server is healthy
✓ Chat completion successful
Response: MLOps is...
Tokens: 150
Time: 2.3s
```

### Step 3: Gradio 웹 UI 실행

```bash
# 터미널 3: Gradio 인터페이스
python src/serve/03_gradio_vllm_demo.py
```

브라우저에서 접속: http://localhost:7860

---

## 상세 가이드

### 1. vLLM 서버 (01_vllm_server.py)

#### 기본 실행

```bash
python src/serve/01_vllm_server.py
```

#### 고급 옵션

```bash
python src/serve/01_vllm_server.py \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 4096 \
  --tensor-parallel-size 1
```

#### LoRA 어댑터 사용

Fine-tuned 모델 (LoRA/QLoRA)을 서빙:

```bash
python src/serve/01_vllm_server.py \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --enable-lora \
  --lora-modules custom-lora=./models/fine-tuned/lora-mistral-custom
```

#### Multi-GPU 사용

```bash
python src/serve/01_vllm_server.py \
  --tensor-parallel-size 2  # 2개 GPU 사용
```

---

### 2. API 클라이언트 (02_vllm_client.py)

#### Python 코드에서 사용

```python
from src.serve.vllm_client import VLLMClient

# 클라이언트 초기화
client = VLLMClient(base_url="http://localhost:8000/v1")

# 채팅 완성
messages = [
    {"role": "user", "content": "What is MLOps?"}
]

response = client.chat_completion(
    messages=messages,
    max_tokens=200,
    temperature=0.7
)

print(response["content"])
```

#### 스트리밍 모드

```python
response = client.chat_completion(
    messages=messages,
    stream=True
)

for chunk in response:
    print(chunk, end="", flush=True)
```

---

### 3. Gradio 웹 UI (03_gradio_vllm_demo.py)

#### 실행

```bash
python src/serve/03_gradio_vllm_demo.py
```

#### 주요 기능

- **실시간 채팅**: 스트리밍 모드 지원
- **파라미터 조정**: Temperature, Top-p, Max tokens
- **시스템 프롬프트**: AI 역할 커스터마이징
- **대화 기록**: 컨텍스트 유지
- **예제 질문**: 빠른 테스트

---

### 4. FastAPI 서버 (04_fastapi_server.py)

vLLM을 래핑하여 인증, 로깅 등 추가 기능 제공

#### 실행

```bash
python src/serve/04_fastapi_server.py
```

#### API 문서

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

#### 엔드포인트

```bash
# 헬스 체크
curl http://localhost:8080/health

# 모델 목록
curl http://localhost:8080/v1/models

# 채팅 완성
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

#### 인증 활성화

`.env` 파일:
```bash
ENABLE_AUTH=true
API_KEY=your-secret-key
```

요청 시:
```bash
curl http://localhost:8080/v1/chat/completions \
  -H "X-API-Key: your-secret-key" \
  -H "Content-Type: application/json" \
  -d '...'
```

---

### 5. 프롬프트 템플릿 (05_prompt_templates.py)

#### 사용 예제

```python
from src.serve.prompt_templates import (
    PromptTemplate,
    PromptType,
    create_mlops_chat_prompt
)

# MLOps 전문 프롬프트
messages = create_mlops_chat_prompt(
    "How do I deploy ML models to production?"
)

# 코드 생성 프롬프트
from src.serve.prompt_templates import create_code_gen_prompt

messages = create_code_gen_prompt(
    description="function to calculate accuracy",
    language="python",
    requirements=["Handle edge cases", "Include docstring"]
)
```

#### 사용 가능한 템플릿

```python
# 템플릿 목록 확인
python src/serve/05_prompt_templates.py
```

- System Prompts: general, mlops, code_generation, debugging, etc.
- Task Templates: mlops_deployment, code_generation, debugging_help, etc.
- Few-Shot Examples: mlops_qa, code_generation

---

### 6. 성능 벤치마크 (06_benchmark_vllm.py)

#### 실행

```bash
python src/serve/06_benchmark_vllm.py
```

#### 벤치마크 종류

1. **Latency Benchmark**: 순차 요청 지연시간
2. **Throughput Benchmark**: 병렬 처리량
3. **Stress Test**: 부하 테스트

#### 결과 예시

```
Latency Benchmark:
  Mean latency: 0.85s
  P95 latency: 1.2s
  Tokens/sec: 125.3

Throughput Benchmark:
  Requests/sec: 8.5
  Tokens/sec: 1050.2
  Concurrent requests: 4

Stress Test:
  Duration: 60s
  Completed requests: 512
  Success rate: 99.8%
  Requests/sec: 8.5
```

---

### 7. LangChain 통합 (07_langchain_pipeline.py)

#### 실행

```bash
python src/serve/07_langchain_pipeline.py
```

#### 기능

1. **Simple Chat**: 기본 채팅
2. **Q&A Chain**: 질문-답변 체인
3. **RAG**: 문서 기반 검색 증강 생성
4. **Conversation**: 대화 기록 유지
5. **Custom Pipelines**: 코드 리뷰 등

#### 사용 예제

```python
from src.serve.langchain_pipeline import VLLMLangChain

# 초기화
vllm = VLLMLangChain(base_url="http://localhost:8000/v1")

# Q&A 체인
qa_chain = vllm.create_qa_chain(
    system_prompt="You are an MLOps expert."
)
response = qa_chain.invoke({"question": "What is model drift?"})

# RAG 체인
documents = ["Document 1...", "Document 2..."]
rag_chain = vllm.create_rag_chain(documents)
response = rag_chain.invoke("Your question")
```

---

## 고급 기능

### Fine-tuned 모델 서빙

#### LoRA 모델

```bash
python src/serve/01_vllm_server.py \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --enable-lora \
  --lora-modules my-lora=./models/fine-tuned/lora-model
```

#### 전체 Fine-tuned 모델

```bash
python src/serve/01_vllm_server.py \
  --model ./models/fine-tuned/my-full-model
```

### 성능 최적화

#### GPU 메모리 최적화

```bash
# 메모리 사용률 조정 (기본: 0.9)
--gpu-memory-utilization 0.95  # 더 많이 사용
--gpu-memory-utilization 0.8   # 여유 확보
```

#### 시퀀스 길이 제한

```bash
# 최대 시퀀스 길이 설정
--max-model-len 2048  # 메모리 절약
--max-model-len 8192  # 긴 컨텍스트
```

#### 배치 처리

```bash
# vLLM은 자동으로 배치 처리
# 동시 요청이 많을수록 효율적
```

### 모니터링

#### Prometheus 메트릭

FastAPI 서버 사용 시:

```bash
# 메트릭 엔드포인트
curl http://localhost:8080/metrics
```

#### 로그 확인

```bash
# vLLM 서버 로그
# 표준 출력으로 출력됨

# FastAPI 로그
# INFO 레벨로 자동 로깅
```

---

## 워크플로우 예제

### Workflow 1: 개발 환경

```bash
# 1. vLLM 서버 시작
python src/serve/01_vllm_server.py

# 2. Gradio UI 시작 (다른 터미널)
python src/serve/03_gradio_vllm_demo.py

# 3. 브라우저에서 테스트
# http://localhost:7860
```

### Workflow 2: 프로덕션 환경

```bash
# 1. vLLM 서버 시작 (백그라운드)
nohup python src/serve/01_vllm_server.py \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --gpu-memory-utilization 0.9 \
  > vllm.log 2>&1 &

# 2. FastAPI 래퍼 시작 (백그라운드)
nohup python src/serve/04_fastapi_server.py \
  > fastapi.log 2>&1 &

# 3. 벤치마크 실행
python src/serve/06_benchmark_vllm.py
```

### Workflow 3: Fine-tuned 모델 배포

```bash
# 1. LoRA 모델 학습 (Phase 2)
python src/train/02_qlora_finetune.py

# 2. vLLM 서버 시작 (LoRA 사용)
python src/serve/01_vllm_server.py \
  --enable-lora \
  --lora-modules custom=./models/fine-tuned/qlora-mistral-custom

# 3. 테스트
python src/serve/02_vllm_client.py test
```

---

## 트러블슈팅

### 문제 1: vLLM 서버가 시작되지 않음

**증상**:
```
ImportError: No module named 'vllm'
```

**해결**:
```bash
pip install vllm>=0.2.6
```

---

### 문제 2: CUDA Out of Memory

**증상**:
```
torch.cuda.OutOfMemoryError: CUDA out of memory
```

**해결**:
```bash
# GPU 메모리 사용률 낮추기
python src/serve/01_vllm_server.py --gpu-memory-utilization 0.8

# 최대 시퀀스 길이 줄이기
python src/serve/01_vllm_server.py --max-model-len 2048

# 4-bit 양자화 사용 (향후 지원)
```

---

### 문제 3: 클라이언트가 서버에 연결되지 않음

**증상**:
```
✗ Server not responding
```

**해결**:
```bash
# 1. 서버가 실행 중인지 확인
curl http://localhost:8000/health

# 2. 포트 확인
netstat -an | grep 8000

# 3. 방화벽 확인
sudo ufw status

# 4. URL 확인
# .env 파일의 VLLM_BASE_URL 확인
```

---

### 문제 4: 느린 추론 속도

**해결**:
```bash
# 1. GPU 메모리 사용률 증가
--gpu-memory-utilization 0.95

# 2. Multi-GPU 사용
--tensor-parallel-size 2

# 3. 배치 처리 확인
# 동시에 여러 요청을 보내면 자동으로 배치 처리됨

# 4. 벤치마크로 확인
python src/serve/06_benchmark_vllm.py
```

---

### 문제 5: LoRA 모델이 로드되지 않음

**증상**:
```
Error loading LoRA adapter
```

**해결**:
```bash
# 1. LoRA 경로 확인
ls -la ./models/fine-tuned/lora-model

# 2. adapter_config.json 확인
cat ./models/fine-tuned/lora-model/adapter_config.json

# 3. 베이스 모델과 호환성 확인
# LoRA는 학습에 사용한 베이스 모델과 동일해야 함

# 4. 전체 경로 사용
--lora-modules custom-lora=/absolute/path/to/lora
```

---

## 성능 참고치

### LLaMA-3-8B-Instruct (RTX 5090, 31GB VRAM)

| 설정 | VRAM | Latency | Throughput |
|------|------|---------|------------|
| FP16 | ~14GB | 0.8s | 120 tokens/s |
| 4-bit | ~6GB | 1.2s | 80 tokens/s |
| FP16 + LoRA | ~15GB | 0.9s | 110 tokens/s |

### 권장 설정

| 사용 목적 | GPU | 설정 |
|-----------|-----|------|
| 개발/테스트 | 8GB+ | 4-bit, --gpu-memory-utilization 0.8 |
| 프로덕션 | 16GB+ | FP16, --gpu-memory-utilization 0.9 |
| 고성능 | 24GB+ | FP16, Multi-GPU |

---

## 다음 단계

### Phase 4: 프로덕션화 (예정)

1. **Docker 컨테이너화**
   ```bash
   deployment/docker/Dockerfile.serve
   docker-compose up vllm-server
   ```

2. **Kubernetes 배포**
   ```bash
   kubectl apply -f deployment/k8s/vllm-deployment.yaml
   ```

3. **모니터링 시스템**
   - Prometheus + Grafana
   - 메트릭 수집 및 대시보드

4. **CI/CD 파이프라인**
   - 자동 배포
   - A/B 테스트
   - 카나리 배포

---

## 참고 자료

### 공식 문서

- [vLLM Documentation](https://vllm.readthedocs.io/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [LangChain Documentation](https://python.langchain.com/)

### 관련 파일

- `PROJECT_STATUS.md` - 프로젝트 전체 현황
- `README.md` - 프로젝트 개요
- `QUICKSTART.md` - 빠른 시작 가이드

---

## 체크리스트

Phase 3 완료 체크리스트:

- [ ] vLLM 서버 실행 성공
- [ ] 클라이언트 테스트 성공
- [ ] Gradio UI 실행 및 테스트
- [ ] FastAPI 서버 실행
- [ ] 프롬프트 템플릿 테스트
- [ ] 벤치마크 실행 및 결과 확인
- [ ] LangChain 통합 테스트
- [ ] Fine-tuned 모델 서빙 (선택)
- [ ] 성능 최적화 (선택)

---

**작성 완료**: 2025-12-18
**작성자**: Claude Code Agent
**버전**: v1.0

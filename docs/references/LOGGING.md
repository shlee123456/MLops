# 세분화된 로깅 시스템 가이드

이 프로젝트는 학습 목적으로 설계된 세분화된 로깅 시스템을 제공합니다.

## 로깅 시스템 개요

### 로그 디렉토리 사용 현황 (2026-01-28 기준)

| 디렉토리 | 상태 | 사용 중인 코드 |
|----------|------|---------------|
| `logs/training/` | ✅ 활성 | `src/train/01_lora_finetune.py`, `02_qlora_finetune.py` |
| `logs/inference/` | ⚠️ 미사용 | 없음 (`InferenceLogger` 정의만 존재) |
| `logs/system/` | ✅ 활성 | `src/train/01_lora_finetune.py`, `02_qlora_finetune.py`, `gpu_monitor.py` |
| `logs/fastapi/` | ✅ 활성 | `src/serve/main.py` (FastAPI 서비스) |
| `logs/vllm/` | ✅ 활성 | Docker 컨테이너 (vLLM 서비스) |
| `logs/mlflow/` | ✅ 활성 | Docker 컨테이너 (MLflow 서비스) |

**참고:**
- `logs/inference/`는 현재 사용되지 않지만, 모니터링 설정(Promtail/Alloy)에는 포함되어 있음
- 향후 vLLM 서비스에 `InferenceLogger`를 통합하여 추론 로그를 생성할 수 있음

### 아키텍처

```
Application Code
      │
      ├─> structlog (JSON formatting)
      │
      ├─> Log Files (./logs/)
      │        │
      │        ├─> training/*.log
      │        ├─> inference/*.log
      │        ├─> system/*.log
      │        └─> api/*.log
      │
      ├─> Promtail (Log Collector)
      │
      ├─> Loki (Log Storage)
      │
      └─> Grafana (Visualization)
```

## 로그 타입별 상세

### 1. Training Logs

**목적:** 학습 과정의 모든 메트릭을 추적

**로그 위치:** `logs/training/`

**사용 현황:**
- ✅ **활성 사용 중**
- `src/train/01_lora_finetune.py` - LoRA 학습 시 사용
- `src/train/02_qlora_finetune.py` - QLoRA 학습 시 사용
- `src/train/train_with_logging_example.py` - 로깅 예제 스크립트

**주요 정보:**
- Epoch/Step 진행 상황
- Loss 값
- Learning rate
- GPU 메모리 사용량
- 검증 메트릭

**JSON 스키마:**
```json
{
  "timestamp": "2025-12-20T12:00:00Z",
  "level": "INFO",
  "message": "training_step",
  "epoch": 1,
  "step": 100,
  "loss": 0.234,
  "learning_rate": 0.0001,
  "gpu_memory_used": 14336,
  "gpu_memory_total": 31744
}
```

**Python 예제:**
```python
from src.utils.logging_utils import TrainingLogger

logger = TrainingLogger("llama3_qlora", log_dir="./logs")

# Epoch 시작
logger.log_epoch_start(epoch=1, total_epochs=3)

# Training step
logger.log_step(
    epoch=1,
    step=100,
    loss=0.234,
    learning_rate=0.0001,
    gpu_memory_used=14336,
    gpu_memory_total=31744
)

# Validation
logger.log_validation(
    epoch=1,
    val_loss=0.245,
    val_accuracy=0.89
)

# Epoch 종료
logger.log_epoch_end(
    epoch=1,
    avg_loss=0.240,
    time_elapsed=3600
)
```

### 2. Inference Logs

**목적:** 추론 성능 및 요청 추적

**로그 위치:** `logs/inference/`

**사용 현황:**
- ⚠️ **미사용** - `InferenceLogger` 클래스는 `src/utils/logging_utils.py`에 정의되어 있으나, 현재 어떤 코드에서도 사용하지 않음
- 디렉토리는 Promtail/Alloy 모니터링 설정에 포함되어 있음
- 향후 vLLM 또는 FastAPI 서비스에 추론 로깅을 추가할 경우 사용 가능

**주요 정보:**
- Request ID (추적용)
- 요청 프롬프트 길이
- 생성된 토큰 수
- 레이턴시 (ms)
- Tokens per second

**JSON 스키마:**
```json
{
  "timestamp": "2025-12-20T12:00:00Z",
  "level": "INFO",
  "message": "inference_response",
  "request_id": "req_abc123",
  "latency_ms": 234.5,
  "tokens_generated": 50,
  "tokens_per_second": 213.2,
  "model_name": "llama-3-8b"
}
```

**Python 예제:**
```python
from src.utils.logging_utils import InferenceLogger
import uuid
import time

logger = InferenceLogger("vllm_server", log_dir="./logs")

# 요청 시작
request_id = str(uuid.uuid4())
prompt = "What is machine learning?"

logger.log_request(
    request_id=request_id,
    prompt=prompt,
    model_name="llama-3-8b"
)

# 추론 실행
start_time = time.time()
response = model.generate(prompt)
latency_ms = (time.time() - start_time) * 1000

# 응답 로깅
logger.log_response(
    request_id=request_id,
    latency_ms=latency_ms,
    tokens_generated=len(response),
    model_name="llama-3-8b"
)
```

### 3. System Logs

**목적:** 하드웨어 리소스 모니터링

**로그 위치:** `logs/system/`

**사용 현황:**
- ✅ **활성 사용 중**
- `src/train/01_lora_finetune.py` - 학습 중 시스템 이벤트 로깅
- `src/train/02_qlora_finetune.py` - 학습 중 시스템 이벤트 로깅
- `src/train/train_with_logging_example.py` - GPU 모니터링 예제
- `src/utils/gpu_monitor.py` - `GPUMonitor` 클래스를 통한 GPU 메트릭 로깅

**주요 정보:**
- GPU 메트릭 (메모리, 사용률, 온도, 전력)
- CPU/메모리 사용률
- 디스크 사용량

**JSON 스키마:**
```json
{
  "timestamp": "2025-12-20T12:00:00Z",
  "level": "INFO",
  "message": "gpu_metrics",
  "gpu_id": 0,
  "gpu_memory_used": 14336,
  "gpu_memory_total": 31744,
  "gpu_memory_percent": 45.2,
  "gpu_utilization": 78.5,
  "temperature": 65,
  "power_watts": 280.5
}
```

**Python 예제:**
```python
from src.utils.gpu_monitor import GPUMonitor

# 자동 모니터링 (백그라운드)
monitor = GPUMonitor(log_dir="./logs", interval=10)
monitor.start_monitoring()  # 10초마다 자동 로깅

# 또는 수동 로깅
monitor.log_all_metrics()
```

### 4. API Logs

**목적:** HTTP API 요청/응답 추적

**로그 위치:** `logs/fastapi/` (또는 `logs/api/`)

**사용 현황:**
- ✅ **활성 사용 중** (실제 경로: `logs/fastapi/`)
- `src/serve/main.py` - FastAPI 서비스가 `src/serve/core/logging.py`의 `RequestLoggingMiddleware`를 통해 자동 로깅
- Docker Compose 환경변수 `LOG_DIR=/logs` 필요
- 주의: `logging_utils.py`의 `APILogger` 클래스와는 별개로, FastAPI는 독립적인 로깅 설정 사용

**주요 정보:**
- HTTP 메서드 및 경로
- 상태 코드
- 처리 시간
- 요청/응답 크기

**JSON 스키마:**
```json
{
  "timestamp": "2025-12-20T12:00:00Z",
  "level": "INFO",
  "message": "api_response",
  "request_id": "req_xyz789",
  "method": "POST",
  "path": "/v1/chat/completions",
  "status_code": 200,
  "duration_ms": 234.5
}
```

**Python 예제 (FastAPI):**
```python
from fastapi import FastAPI, Request
from src.utils.logging_utils import APILogger
import time
import uuid

app = FastAPI()
logger = APILogger("fastapi_server", log_dir="./logs")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())

    # 요청 로깅
    logger.log_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path
    )

    # 처리
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    # 응답 로깅
    logger.log_response(
        request_id=request_id,
        status_code=response.status_code,
        duration_ms=duration_ms
    )

    return response
```

## Grafana에서 로그 활용

### LogQL 쿼리 예제

#### 1. 학습 진행 상황 추적

```logql
# 최근 Loss 값들
{job="training"} | json | line_format "Step {{.step}}: Loss {{.loss}}"

# Loss가 특정 값 이하인 경우
{job="training"} | json | loss < 0.1

# 특정 Epoch의 모든 로그
{job="training"} | json | epoch="1"
```

#### 2. 추론 성능 분석

```logql
# 평균 레이턴시 (5분 간격)
avg_over_time({job="inference"} | json | unwrap latency_ms [5m])

# 높은 레이턴시 요청 찾기
{job="inference"} | json | latency_ms > 1000

# Request ID로 추적
{job="inference", request_id="req_abc123"}
```

#### 3. GPU 모니터링

```logql
# GPU 메모리 사용률
{job="system"} | json | line_format "GPU {{.gpu_id}}: {{.gpu_memory_percent}}%"

# GPU 온도 경고 (70도 이상)
{job="system"} | json | temperature > 70

# 특정 GPU의 메트릭만
{job="system", gpu_id="0"}
```

#### 4. 에러 추적

```logql
# 모든 에러 로그
{service="mlops", level="ERROR"}

# 특정 서비스의 에러만
{job="training", level="ERROR"}

# 에러 메시지 검색
{level="ERROR"} |= "out of memory"
```

### Grafana 알림 설정

#### 예제 1: GPU 메모리 경고

```logql
Query: avg(max_over_time({job="system"} | json | unwrap gpu_memory_percent [1m]))
Condition: WHEN last() > 90
Alert: GPU memory usage is above 90%
```

#### 예제 2: 높은 추론 레이턴시

```logql
Query: avg(rate({job="inference"} | json | unwrap latency_ms [5m]))
Condition: WHEN last() > 1000
Alert: Average inference latency is above 1000ms
```

## 로깅 베스트 프랙티스

### 1. 구조화된 정보 포함

```python
# ❌ 나쁜 예
logger.info("Loss is 0.234")

# ✅ 좋은 예
logger.log_step(
    epoch=1,
    step=100,
    loss=0.234,
    learning_rate=0.0001
)
```

### 2. Request ID 사용

```python
# 요청-응답 추적을 위해 항상 request_id 포함
request_id = str(uuid.uuid4())

logger.log_request(request_id=request_id, ...)
# ... 처리 ...
logger.log_response(request_id=request_id, ...)
```

### 3. 적절한 로그 레벨

- **DEBUG**: 개발 중 상세 정보
- **INFO**: 일반 운영 정보 (기본)
- **WARNING**: 주의가 필요한 상황
- **ERROR**: 에러 발생

```python
logger.logger.debug("Detailed debug info")
logger.logger.info("Normal operation")
logger.logger.warning("Something unusual")
logger.logger.error("Error occurred")
```

### 4. 민감한 정보 제외

```python
# ❌ 비밀번호나 토큰 로깅 금지
logger.log_request(api_key="secret_key_123")

# ✅ 마스킹 또는 생략
logger.log_request(api_key="***masked***")
```

## 로그 분석 예제

### 1. 학습 Loss 추이 분석

Grafana에서:
1. Add Panel > Graph
2. 데이터소스: Loki
3. 쿼리:
```logql
rate({job="training"} | json | unwrap loss [1m])
```

### 2. 추론 성능 대시보드

```logql
# QPS (초당 쿼리 수)
sum(rate({job="inference"}[1m]))

# 평균 레이턴시
avg(rate({job="inference"} | json | unwrap latency_ms [5m]))

# P95 레이턴시
quantile_over_time(0.95, {job="inference"} | json | unwrap latency_ms [5m])
```

### 3. GPU 사용률 히트맵

```logql
max by (gpu_id) (rate({job="system"} | json | unwrap gpu_utilization [1m]))
```

## 로그 보관 및 관리

### 자동 로그 로테이션

로그 파일은 타임스탬프가 포함되어 자동으로 분리됩니다:

```
logs/training/
├── llama3_qlora_20251220_120000.log
├── llama3_qlora_20251220_180000.log
└── llama3_qlora_20251221_090000.log
```

### 오래된 로그 정리

```bash
# 7일 이상된 로그 삭제
find logs/ -name "*.log" -mtime +7 -delete

# 자동화 (crontab)
0 2 * * * find /path/to/logs -name "*.log" -mtime +7 -delete
```

### 로그 백업

```bash
# 일별 백업
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# S3로 업로드 (선택)
aws s3 cp logs_backup_*.tar.gz s3://my-bucket/logs/
```

## 디버깅 팁

### 1. 로그 파일 직접 조회

```bash
# 실시간 로그 스트림
tail -f logs/training/*.log | jq .

# 특정 필드만 추출
tail -f logs/training/*.log | jq '.loss'

# 에러만 필터링
tail -f logs/training/*.log | jq 'select(.level=="ERROR")'
```

### 2. 로그 검색

```bash
# 특정 step 찾기
grep "\"step\":100" logs/training/*.log | jq .

# Loss가 특정 값 이하인 경우
jq 'select(.loss < 0.1)' logs/training/*.log
```

### 3. 통계 계산

```bash
# 평균 loss 계산
jq -s 'map(.loss) | add/length' logs/training/*.log

# 최소/최대 레이턴시
jq -s 'map(.latency_ms) | min, max' logs/inference/*.log
```

## 참고 자료

- [structlog Documentation](https://www.structlog.org/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [LogQL Guide](https://grafana.com/docs/loki/latest/logql/)
- [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/)

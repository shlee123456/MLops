# 로깅 통합 가이드

기존 학습 코드에 구조화된 로깅을 통합하는 방법입니다.

## 통합 완료된 스크립트

### ✅ QLoRA Fine-tuning (`src/train/02_qlora_finetune.py`)

완전히 통합된 로깅 기능:
- TrainingCallback을 통한 자동 로깅
- Epoch/Step 별 메트릭 추적
- GPU 메모리 및 사용률 모니터링
- 에러 추적
- MLflow와 통합

**실행 방법:**
```bash
# 로컬 실행
python src/train/02_qlora_finetune.py

# Docker로 실행 (권장)
docker-compose run --rm --gpus all \
  -e LOG_DIR=/logs \
  training \
  python /app/src/train/02_qlora_finetune.py
```

**생성되는 로그:**
- `logs/training/qlora-YYYYMMDD-HHMMSS_*.log`: 학습 메트릭
- `logs/system/qlora_training_*.log`: GPU/시스템 메트릭

### LoRA Fine-tuning (`src/train/01_lora_finetune.py`)

LoRA 스크립트는 QLoRA와 동일한 패턴으로 통합할 수 있습니다.
백업 파일이 생성되어 있으므로 필요시 참고하세요.

## 사용 예제

### 1. 간단한 테스트

```bash
# 로깅 시스템 테스트 (GPU 불필요)
./test_logging.sh
```

또는:

```bash
# Python 직접 실행
python src/train/train_with_logging_example.py
```

### 2. 실제 학습에서 로깅 사용

```python
from src.utils.logging_utils import TrainingLogger, SystemLogger
from transformers import TrainerCallback

# 1. 로거 초기화
training_logger = TrainingLogger("my_experiment", log_dir="./logs")
system_logger = SystemLogger("my_system", log_dir="./logs")

# 2. Callback 클래스 정의
class LoggingCallback(TrainerCallback):
    def __init__(self, logger, system_logger):
        self.logger = logger
        self.system_logger = system_logger

    def on_epoch_begin(self, args, state, control, **kwargs):
        self.logger.log_epoch_start(
            epoch=int(state.epoch),
            total_epochs=int(args.num_train_epochs)
        )

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            loss = logs.get('loss')
            lr = logs.get('learning_rate')

            if loss and lr:
                self.logger.log_step(
                    epoch=int(state.epoch),
                    step=state.global_step,
                    loss=loss,
                    learning_rate=lr
                )

            # GPU 메트릭
            if torch.cuda.is_available():
                self.system_logger.log_gpu_metrics(
                    gpu_id=0,
                    gpu_memory_used=torch.cuda.memory_allocated(),
                    gpu_memory_total=torch.cuda.get_device_properties(0).total_memory,
                    gpu_utilization=(torch.cuda.memory_allocated() /
                                    torch.cuda.get_device_properties(0).total_memory * 100)
                )

# 3. Trainer에 Callback 추가
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    callbacks=[LoggingCallback(training_logger, system_logger)]
)

# 4. 학습 실행
trainer.train()
```

## 로그 확인

### 1. 로컬 파일 확인

```bash
# 실시간 로그 스트림
tail -f logs/training/*.log | jq .

# 특정 필드만 추출
tail -f logs/training/*.log | jq '.loss'

# 최근 로그 확인
cat $(ls -t logs/training/*.log | head -1) | jq .
```

### 2. Grafana에서 확인

```bash
# Docker 서비스 시작
docker-compose up -d

# Grafana 접속
# http://localhost:3000 (admin/admin)
```

**Grafana Loki 쿼리:**
```logql
# 모든 학습 로그
{job="training"}

# Loss 값만
{job="training"} | json | loss != ""

# 에러만
{job="training", level="ERROR"}

# GPU 메모리 사용률
{job="system"} | json | line_format "GPU Memory: {{.gpu_memory_percent}}%"
```

### 3. 대시보드

사전 구성된 대시보드:
- **Training Metrics**: 학습 진행 상황, Loss 추이
- **System Overview**: GPU/CPU 사용률
- **Unified Logs**: 모든 로그 통합 뷰

## 로그 구조

### Training Log 예제
```json
{
  "timestamp": "2025-12-20T12:00:00Z",
  "level": "INFO",
  "message": "training_step",
  "epoch": 1,
  "step": 100,
  "loss": 0.234,
  "learning_rate": 0.0001,
  "gpu_memory_gb": 14.5
}
```

### System Log 예제
```json
{
  "timestamp": "2025-12-20T12:00:00Z",
  "level": "INFO",
  "message": "gpu_metrics",
  "gpu_id": 0,
  "gpu_memory_used": 15360000000,
  "gpu_memory_total": 33554432000,
  "gpu_memory_percent": 45.8,
  "gpu_utilization": 78.5,
  "temperature": 65,
  "power_watts": 280.5
}
```

## 커스텀 로깅 추가

### 1. 추론 로깅

```python
from src.utils.logging_utils import InferenceLogger

logger = InferenceLogger("my_service", log_dir="./logs")

# 요청 로깅
request_id = "req_123"
logger.log_request(
    request_id=request_id,
    prompt="What is AI?",
    model_name="llama-3-8b"
)

# 응답 로깅
logger.log_response(
    request_id=request_id,
    latency_ms=234.5,
    tokens_generated=50
)
```

### 2. API 로깅 (FastAPI)

```python
from src.utils.logging_utils import APILogger
from fastapi import FastAPI, Request
import uuid
import time

app = FastAPI()
logger = APILogger("fastapi", log_dir="./logs")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())

    logger.log_request(
        request_id=request_id,
        method=request.method,
        path=request.url.path
    )

    start = time.time()
    response = await call_next(request)
    duration = (time.time() - start) * 1000

    logger.log_response(
        request_id=request_id,
        status_code=response.status_code,
        duration_ms=duration
    )

    return response
```

### 3. GPU 모니터링

```python
from src.utils.gpu_monitor import GPUMonitor

# 자동 모니터링 (백그라운드)
with GPUMonitor(log_dir="./logs", interval=10) as monitor:
    monitor.start_monitoring()  # 10초마다 자동 로깅

# 또는 수동 로깅
monitor = GPUMonitor(log_dir="./logs")
monitor.log_all_metrics()
```

## 트러블슈팅

### 로그가 생성되지 않음

```bash
# 로그 디렉토리 확인
ls -la logs/

# 권한 확인
chmod -R 755 logs/

# Python 경로 확인
python -c "import sys; print(sys.path)"
```

### Import 에러

```bash
# utils 패키지 확인
ls -la src/utils/

# PYTHONPATH 설정
export PYTHONPATH=/home/shlee/mlops:$PYTHONPATH
python src/train/02_qlora_finetune.py
```

### JSON 파싱 에러

```bash
# 로그 파일 검증
cat logs/training/*.log | jq empty

# 잘못된 JSON 찾기
for f in logs/training/*.log; do
    jq empty < "$f" 2>&1 | grep -q "parse error" && echo "Error in $f"
done
```

## 베스트 프랙티스

1. **항상 구조화된 로깅 사용**
   ```python
   # ❌ 나쁜 예
   print(f"Loss: {loss}")

   # ✅ 좋은 예
   logger.log_step(epoch=1, step=100, loss=loss, learning_rate=lr)
   ```

2. **Request ID로 추적**
   ```python
   # 요청-응답 연결
   request_id = str(uuid.uuid4())
   logger.log_request(request_id=request_id, ...)
   # ... 처리 ...
   logger.log_response(request_id=request_id, ...)
   ```

3. **에러 처리**
   ```python
   try:
       train()
   except Exception as e:
       logger.log_error(error=str(e), traceback=traceback.format_exc())
       raise
   ```

4. **주기적인 GPU 모니터링**
   ```python
   # 학습 중 GPU 상태 추적
   if step % 10 == 0:
       system_logger.log_gpu_metrics(...)
   ```

## 참고 문서

- [로깅 시스템 가이드](LOGGING_GUIDE.md)
- [로깅 유틸리티 API](src/utils/logging_utils.py)
- [GPU 모니터링](src/utils/gpu_monitor.py)
- [Grafana 대시보드](deployment/configs/grafana/)

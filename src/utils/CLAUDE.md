# src/utils/ - 유틸리티

구조화된 로깅 및 GPU 모니터링

## 파일

| 파일 | 설명 |
|------|------|
| `logging_utils.py` | JSON 로깅 (structlog) |
| `gpu_monitor.py` | GPU 메트릭 |
| `__init__.py` | 패키지 |

## Import 경로

```python
# 프로젝트 루트에서 실행 시
from src.utils.logging_utils import TrainingLogger, LogType

# src/ 내부에서 실행 시 (상대 경로)
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from src.utils.logging_utils import TrainingLogger
```

## 로그 타입

```python
class LogType:
    TRAINING = "training"
    INFERENCE = "inference"
    SYSTEM = "system"
    API = "api"
```

## 로거 클래스 및 주요 메서드

### TrainingLogger
```python
logger = TrainingLogger("experiment-name")
logger.log_epoch_start(epoch=1, total_epochs=3)
logger.log_step(epoch=1, step=100, loss=0.5, learning_rate=2e-4)
logger.log_epoch_end(epoch=1, avg_loss=0.45)
logger.log_validation(epoch=1, val_loss=0.48)
logger.log_error("OOM 발생")
```

### InferenceLogger
```python
logger = InferenceLogger("vllm-server")
logger.log_request(request_id="abc", prompt="질문")
logger.log_response(request_id="abc", latency_ms=150, tokens_generated=50)
logger.log_error(request_id="abc", error="타임아웃")
```

### SystemLogger
```python
logger = SystemLogger("system-monitor")
logger.log_gpu_metrics(gpu_id=0, gpu_memory_used=8000, gpu_memory_total=31000, gpu_utilization=80.5)
logger.log_system_metrics(cpu_percent=45.0, memory_percent=60.0, disk_percent=30.0)
```

### APILogger
```python
logger = APILogger("fastapi")
logger.log_request(request_id="xyz", method="POST", path="/v1/chat")
logger.log_response(request_id="xyz", status_code=200, duration_ms=250)
```

## 로그 저장 위치

```
logs/
├── training/    # 학습 (epoch, loss)
├── inference/   # 추론 (latency, tokens/sec)
├── system/      # GPU, CPU, 메모리
└── api/         # HTTP 요청/응답
```

## Loki/Grafana 연동

JSON 포맷 → Promtail → Loki → Grafana

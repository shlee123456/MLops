# Docker Compose 빠른 시작 가이드

세분화된 로깅 시스템을 갖춘 MLOps 플랫폼 빠른 시작 가이드입니다.

## 전제 조건

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker Runtime (GPU 사용 시)
- 최소 50GB 디스크 공간
- 최소 16GB RAM (권장: 32GB)

## 1분 시작하기

```bash
# 1. 환경 변수 설정
cp .env.docker .env

# 2. 로그 디렉토리 생성
mkdir -p logs/{training,inference,system,mlflow,vllm,fastapi}

# 3. 전체 스택 시작
docker-compose up -d

# 4. 서비스 상태 확인
docker-compose ps
```

## 웹 UI 접속

서비스가 시작되면 다음 URL로 접속할 수 있습니다:

| 서비스 | URL | 인증 정보 |
|--------|-----|----------|
| Grafana (시각화) | http://localhost:3000 | admin / admin |
| MLflow (실험 추적) | http://localhost:5000 | - |
| Prometheus (메트릭) | http://localhost:9090 | - |
| MinIO Console | http://localhost:9001 | minio / minio123 |
| FastAPI Docs | http://localhost:8080/docs | - |

## 주요 기능

### 1. 세분화된 로깅 시스템

모든 로그는 JSON 형식으로 구조화되어 저장되며, Grafana에서 실시간으로 확인할 수 있습니다.

**로그 타입:**
- **Training**: 학습 메트릭 (loss, learning rate, epoch, step)
- **Inference**: 추론 성능 (latency, tokens/sec, request tracking)
- **System**: GPU/CPU 메트릭
- **API**: HTTP 요청/응답 로그

**로그 저장 위치:**
```
logs/
├── training/       # 학습 로그
├── inference/      # 추론 로그
├── system/         # 시스템 로그
├── mlflow/         # MLflow 서버 로그
├── vllm/           # vLLM 서버 로그
└── fastapi/        # API 서버 로그
```

### 2. Grafana 대시보드

사전 구성된 4개의 대시보드:

1. **System Overview** - 전체 시스템 상태
   - GPU 메모리/사용률
   - CPU/메모리 사용량
   - 컨테이너 리소스

2. **Training Metrics** - 학습 모니터링
   - 실시간 학습 로그
   - Loss 추이
   - 현재 Step/Epoch

3. **Inference Metrics** - 추론 성능
   - QPS (Queries Per Second)
   - 레이턴시 (p50, p95)
   - 토큰 생성 속도

4. **Unified Logs** - 통합 로그 뷰
   - 모든 서비스 로그 통합
   - 레벨별 필터링
   - 에러 추적

### 3. 실험 추적 (MLflow)

학습 실험을 자동으로 추적하고 비교할 수 있습니다.

```bash
# MLflow UI 접속
# http://localhost:5000
```

## 학습 실행 예제

### 로깅이 통합된 학습 실행

```bash
# QLoRA Fine-tuning 실행
docker-compose run --rm \
  --gpus all \
  -e MLFLOW_TRACKING_URI=http://mlflow-server:5000 \
  -v $(pwd)/models:/models \
  -v $(pwd)/data:/data \
  -v $(pwd)/logs:/logs \
  training \
  python /app/src/train/02_qlora_finetune.py
```

학습 중:
- **실시간 로그**: Grafana > Training Metrics 대시보드
- **메트릭**: MLflow UI에서 확인
- **GPU 모니터링**: Grafana > System Overview

### Python 코드에서 로깅 사용

```python
from src.utils.logging_utils import TrainingLogger

# 로거 초기화
logger = TrainingLogger(
    experiment_name="my_experiment",
    log_dir="./logs"
)

# 학습 시작
logger.log_epoch_start(epoch=1, total_epochs=3)

# Step 로깅
for step in range(100):
    loss = train_step()
    logger.log_step(
        epoch=1,
        step=step,
        loss=loss,
        learning_rate=0.0001
    )

# Epoch 종료
logger.log_epoch_end(epoch=1, avg_loss=0.234)
```

## 로그 조회 방법

### Grafana에서 로그 조회

1. Grafana 접속 (http://localhost:3000)
2. 왼쪽 메뉴 > Explore
3. 데이터소스: **Loki** 선택
4. 쿼리 입력:

```logql
# 학습 로그 조회
{job="training"}

# 에러만 보기
{service="mlops", level="ERROR"}

# Loss 값 추출
{job="training"} | json | loss != ""

# 높은 레이턴시 추론 로그
{job="inference"} | json | latency_ms > 1000
```

### 커맨드라인에서 로그 조회

```bash
# 실시간 로그 스트림
docker-compose logs -f vllm-server

# JSON 로그 파일 직접 조회
tail -f logs/training/*.log | jq .
```

## GPU 모니터링

### 실시간 GPU 메트릭

```bash
# GPU 모니터링 스크립트 실행
docker-compose run --rm --gpus all training \
  python /app/src/utils/gpu_monitor.py
```

Grafana에서 확인:
- System Overview > GPU Memory Usage
- System Overview > GPU Utilization

## 서비스 관리

### 개별 서비스 시작/중지

```bash
# MLflow 스택만 시작
docker-compose up -d postgres minio mlflow-server

# Serving 스택만 시작
docker-compose up -d vllm-server fastapi-server

# Monitoring 스택만 시작
docker-compose up -d prometheus grafana loki promtail

# 특정 서비스 중지
docker-compose stop vllm-server

# 특정 서비스 재시작
docker-compose restart fastapi-server
```

### 로그 확인

```bash
# 모든 서비스 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs -f mlflow-server

# 최근 100줄만 보기
docker-compose logs --tail=100 vllm-server
```

### 리소스 사용량 확인

```bash
# 컨테이너 리소스 사용량
docker stats

# 디스크 사용량
docker system df
```

## 데이터 영속성

Docker 볼륨을 사용하여 데이터를 영구 저장합니다:

```bash
# 볼륨 목록
docker volume ls

# 볼륨 상세 정보
docker volume inspect mlops_postgres_data
```

**주요 볼륨:**
- `postgres_data`: MLflow 실험 데이터
- `minio_data`: 모델 아티팩트
- `loki_data`: 로그 데이터
- `prometheus_data`: 메트릭 데이터
- `grafana_data`: 대시보드 설정

## 백업 및 복구

### MLflow 데이터 백업

```bash
# PostgreSQL 백업
docker-compose exec postgres pg_dump -U mlflow mlflow > backup.sql

# 복구
cat backup.sql | docker-compose exec -T postgres psql -U mlflow
```

### 로그 백업

```bash
# 로그 아카이브 생성
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# 오래된 로그 정리 (7일 이전)
find logs/ -name "*.log" -mtime +7 -delete
```

## 트러블슈팅

### GPU가 인식되지 않을 때

```bash
# NVIDIA Docker 확인
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# docker-compose.yml에서 deploy.resources.reservations 확인
```

### 서비스가 시작되지 않을 때

```bash
# 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs [service-name]

# 헬스체크 확인
docker inspect [container-name] | jq '.[0].State.Health'

# 재시작
docker-compose restart [service-name]
```

### 포트 충돌

```bash
# 포트 사용 확인
sudo lsof -i :5000  # MLflow
sudo lsof -i :3000  # Grafana
sudo lsof -i :8000  # vLLM

# .env 파일에서 포트 변경
```

### 디스크 공간 부족

```bash
# Docker 정리
docker system prune -a --volumes

# 로그 정리
find logs/ -name "*.log" -mtime +7 -delete

# 볼륨 확인
docker volume ls
docker volume rm [volume-name]
```

### 로그가 수집되지 않을 때

```bash
# Promtail 상태 확인
docker-compose logs promtail

# Loki 연결 확인
curl http://localhost:3100/ready

# 로그 파일 권한 확인
ls -la logs/
chmod -R 755 logs/
```

## 성능 최적화

### vLLM 메모리 설정

`.env` 파일 수정:

```bash
# GPU 메모리 사용률 (0.0 ~ 1.0)
GPU_MEMORY_UTILIZATION=0.9

# 최대 시퀀스 길이
MAX_MODEL_LEN=4096
```

### Prometheus 보관 기간

`deployment/configs/prometheus/prometheus.yml`:

```yaml
storage:
  tsdb:
    retention.time: 15d    # 15일
    retention.size: 50GB   # 최대 50GB
```

### Loki 보관 기간

`deployment/configs/loki/loki-config.yaml`:

```yaml
limits_config:
  retention_period: 168h   # 7일
```

## 고급 기능

### 커스텀 대시보드 생성

1. Grafana 접속
2. Create > Dashboard
3. Add Panel
4. 데이터소스 선택 (Prometheus 또는 Loki)
5. 쿼리 작성
6. Save Dashboard

### Alerting 설정

1. Grafana > Alerting > Alert Rules
2. New Alert Rule
3. 조건 설정 (예: GPU 메모리 > 90%)
4. Notification Channel 설정

### 멀티 GPU 학습

```bash
docker-compose run --rm \
  --gpus '"device=0,1"' \
  -e CUDA_VISIBLE_DEVICES=0,1 \
  training \
  python /app/src/train/02_qlora_finetune.py
```

## 다음 단계

1. **학습 실행**: 로깅이 통합된 학습 스크립트 실행
2. **Grafana 대시보드**: 실시간 메트릭 확인
3. **로그 분석**: Loki에서 학습 로그 쿼리
4. **실험 비교**: MLflow에서 여러 실험 비교
5. **커스텀 대시보드**: 프로젝트에 맞는 대시보드 생성

## 참고 문서

- [전체 배포 가이드](deployment/README.md)
- [로깅 유틸리티 사용법](src/utils/logging_utils.py)
- [Grafana 대시보드 설정](deployment/configs/grafana/)
- [Prometheus 설정](deployment/configs/prometheus/)

## 지원

문제가 발생하면:
1. 로그 확인: `docker-compose logs`
2. 서비스 상태: `docker-compose ps`
3. 리소스 확인: `docker stats`
4. Grafana에서 에러 로그 조회: `{level="ERROR"}`

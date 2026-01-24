# MLOps Deployment Guide

Docker Compose 기반 MLOps 시스템 배포 가이드입니다.

## 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                     MLOps Platform                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Training   │  │   Serving    │  │   MLflow     │     │
│  │   Service    │  │   Service    │  │   Server     │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│         ┌──────────────────┴──────────────────┐             │
│         │                                      │             │
│  ┌──────▼───────┐                    ┌────────▼────────┐   │
│  │   Logging    │                    │   Monitoring    │   │
│  │   Stack      │                    │   Stack         │   │
│  ├──────────────┤                    ├─────────────────┤   │
│  │ Loki         │                    │ Prometheus      │   │
│  │ Alloy        │◄───────────────────┤ Alloy           │   │
│  │ Grafana      │                    │ Grafana         │   │
│  └──────────────┘                    └─────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

> **Note**: Alloy가 로그 수집(Promtail), 메트릭 수집(node-exporter, cadvisor) 기능을 통합

## 디렉토리 구조

```
deployment/
├── mlflow/
│   └── Dockerfile              # MLflow 서버
├── serving/
│   ├── Dockerfile.vllm         # vLLM GPU 서빙
│   └── Dockerfile.fastapi      # FastAPI 게이트웨이
├── train/
│   └── Dockerfile              # 학습용
└── monitoring/
    └── configs/
        ├── alloy/config.alloy       # 통합 에이전트 (logs + metrics)
        ├── grafana/dashboards/      # 대시보드 JSON
        ├── grafana/provisioning/    # 데이터소스/대시보드 설정
        ├── loki/loki-config.yaml
        └── prometheus/prometheus.yml
```

## Docker Compose 파일

```
docker/
├── docker-compose.yml              # 전체 스택 (include)
├── docker-compose.mlflow.yml       # MLflow Stack
├── docker-compose.serving.yml      # Serving Stack
├── docker-compose.monitoring.yml   # Monitoring Stack
└── .env.example                    # 환경변수 템플릿
```

## 서비스 구성

### Core Services

1. **MLflow Stack**
   - `postgres`: MLflow 백엔드 데이터베이스
   - `minio`: 모델 아티팩트 스토리지
   - `mlflow-server`: 실험 추적 서버
   - 포트: 5050 (MLflow UI), 9000 (MinIO API), 9001 (MinIO Console)

2. **Serving Stack**
   - `vllm-server`: 고성능 LLM 추론 서버
   - `fastapi-server`: RESTful API 게이트웨이
   - 포트: 8000 (vLLM), 8080 (FastAPI)

### Observability Services

3. **Monitoring Stack**
   - `prometheus`: 메트릭 수집 및 저장
   - `loki`: 로그 저장소
   - `alloy`: 통합 에이전트 (로그 + 메트릭 수집)
   - `grafana`: 시각화 대시보드
   - 포트: 9090 (Prometheus), 3100 (Loki), 3000 (Grafana), 12345 (Alloy UI)

## 로그 구조

프로젝트는 세분화된 로깅 시스템을 제공합니다:

### 로그 타입

1. **Training Logs** (`logs/training/`)
   - 학습 진행 상황 (epoch, step, loss)
   - 학습률 변화
   - 검증 메트릭
   - GPU 메모리 사용량

2. **Inference Logs** (`logs/inference/`)
   - 요청/응답 로그
   - 레이턴시 측정
   - 생성된 토큰 수
   - 처리량 (tokens/sec)

3. **System Logs** (`logs/system/`)
   - GPU 메트릭 (사용률, 메모리, 온도, 전력)
   - CPU/메모리 사용률
   - 디스크 사용량

4. **API Logs** (`logs/fastapi/`)
   - HTTP 요청/응답
   - 상태 코드
   - 처리 시간

### 로그 포맷

모든 로그는 구조화된 JSON 형식으로 저장됩니다:

```json
{
  "timestamp": "2025-12-20T12:00:00Z",
  "level": "INFO",
  "message": "training_step",
  "epoch": 1,
  "step": 100,
  "loss": 0.234,
  "learning_rate": 0.0001
}
```

## 시작하기

### 1. 환경 변수 설정

```bash
cp .env.docker .env
# .env 파일 편집
```

### 2. 디렉토리 구조 확인

```bash
# 로그 디렉토리가 자동으로 생성되지만, 권한 확인
mkdir -p logs/{training,inference,system,mlflow,vllm,fastapi}
chmod -R 755 logs/
```

### 3. Docker Compose 실행

#### 전체 스택 시작

```bash
docker compose -f docker/docker-compose.yml up -d
```

#### 개별 스택 실행

```bash
# MLflow 스택
docker compose -f docker/docker-compose.mlflow.yml up -d

# Serving 스택
docker compose -f docker/docker-compose.serving.yml up -d

# Monitoring 스택
docker compose -f docker/docker-compose.monitoring.yml up -d
```

#### 스택 조합 실행

```bash
# MLflow + Serving
docker compose -f docker/docker-compose.mlflow.yml -f docker/docker-compose.serving.yml up -d

# 전체
docker compose -f docker/docker-compose.yml up -d
```

### 4. 서비스 확인

```bash
# 모든 서비스 상태 확인
docker compose -f docker/docker-compose.yml ps

# 로그 확인
docker compose -f docker/docker-compose.serving.yml logs -f vllm-server

# 중지
docker compose -f docker/docker-compose.yml down
```

### 5. 웹 UI 접속

| URL | 서비스 | 계정 |
|-----|--------|------|
| http://localhost:5050 | MLflow UI | - |
| http://localhost:8000/docs | vLLM (OpenAI API) | - |
| http://localhost:8080/docs | FastAPI | - |
| http://localhost:9090 | Prometheus | - |
| http://localhost:3000 | Grafana | admin/admin |
| http://localhost:3100 | Loki | - |
| http://localhost:12345 | Alloy UI | - |
| http://localhost:9001 | MinIO Console | minio/minio123 |

## 학습 실행 (with Logging)

### Docker 내에서 학습 실행

```bash
# Training 컨테이너 빌드 및 실행
docker compose -f docker/docker-compose.yml run --rm \
  -e MLFLOW_TRACKING_URI=http://mlflow-server:5050 \
  -v $(pwd)/models:/models \
  -v $(pwd)/data:/data \
  -v $(pwd)/logs:/logs \
  --gpus all \
  training \
  python /app/src/train/02_qlora_finetune.py
```

학습 중 로그는 자동으로 다음 위치에 저장됩니다:
- JSON 로그: `logs/training/qlora_finetune_YYYYMMDD_HHMMSS.log`
- MLflow 메트릭: http://localhost:5050 에서 확인
- Grafana 대시보드: Training Metrics / Training Detail

## Grafana 대시보드

사전 구성된 대시보드:

### 개요 대시보드

1. **System Overview** (`system-overview.json`)
   - GPU 메모리 사용률
   - GPU 사용률
   - CPU/메모리 사용률
   - 컨테이너 리소스

2. **Training Metrics** (`training-metrics.json`)
   - 학습 로그 스트림
   - 현재 step/epoch
   - Loss 그래프
   - 에러 로그

3. **Inference Metrics** (`inference-metrics.json`)
   - 초당 요청 수 (QPS)
   - 레이턴시 (p50, p95)
   - 생성된 토큰 수
   - 처리량

4. **Logs Dashboard** (`logs-dashboard.json`)
   - 모든 서비스 로그 통합 뷰
   - 로그 레벨별 필터링
   - 시간대별 조회

### 상세 대시보드 (드릴다운)

5. **Inference Detail** (`inference-detail.json`)
   - 엔드포인트별 상세 분석
   - 모델별 성능 비교
   - 요청 패턴 분석
   - 에러 추적

6. **Training Detail** (`training-detail.json`)
   - 실험별 상세 분석
   - 하이퍼파라미터 비교
   - 학습 곡선
   - GPU 메모리 프로파일링

> **드릴다운 워크플로우**: [GRAFANA_DRILLDOWN_WORKFLOW.md](../docs/references/GRAFANA_DRILLDOWN_WORKFLOW.md) 참조

## 로그 조회 (LogQL)

Grafana의 Explore에서 Loki 데이터소스를 선택하여 로그를 조회할 수 있습니다.

### 예제 쿼리

```logql
# 특정 job의 모든 로그
{job="training"}

# 에러 로그만 조회
{job="fastapi", level="ERROR"}

# Loss 값 추출
{job="training"} | json | loss != ""

# 특정 시간대 inference 로그
{job="fastapi"} | json | latency_ms > 1000

# Request ID로 추적
{job="fastapi", request_id="abc123"}

# 특정 엔드포인트 로그
{job="fastapi"} | json | endpoint="/api/v1/chat/completions"

# vLLM 서버 로그
{job="vllm"}
```

## 모니터링 메트릭

### Prometheus 메트릭

주요 메트릭:
- `node_nvidia_gpu_memory_used_bytes`: GPU 메모리 사용량
- `node_nvidia_gpu_utilization`: GPU 사용률
- `container_cpu_usage_seconds_total`: 컨테이너 CPU 사용량
- `http_requests_total`: HTTP 요청 수
- `http_request_duration_seconds`: 요청 처리 시간

### 커스텀 메트릭 추가

애플리케이션에서 Prometheus 클라이언트를 사용하여 커스텀 메트릭을 추가할 수 있습니다.

```python
from prometheus_client import Counter, Histogram

# 요청 카운터
requests_total = Counter('requests_total', 'Total requests')

# 레이턴시 히스토그램
latency = Histogram('request_latency_seconds', 'Request latency')
```

## 데이터 백업

### MLflow 데이터 백업

```bash
# PostgreSQL 백업
docker compose -f docker/docker-compose.mlflow.yml exec postgres \
  pg_dump -U mlflow mlflow > mlflow_backup.sql

# MinIO 백업 (mc 클라이언트 사용)
docker run --rm --network mlops-project_default \
  -v $(pwd):/backup \
  minio/mc alias set myminio http://minio:9000 minio minio123

docker run --rm --network mlops-project_default \
  -v $(pwd):/backup \
  minio/mc cp --recursive myminio/mlflow /backup/mlflow_artifacts
```

### 로그 백업

```bash
# 로그 아카이브
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# Loki 데이터 백업
docker compose -f docker/docker-compose.monitoring.yml exec loki \
  tar -czf /tmp/loki_data.tar.gz /loki
```

### Prometheus 데이터 백업

```bash
# Prometheus 스냅샷 생성
curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot

# 생성된 스냅샷 복사
docker compose -f docker/docker-compose.monitoring.yml exec prometheus \
  tar -czf /tmp/prometheus_snapshot.tar.gz /prometheus/snapshots
```

## 트러블슈팅

### 서비스가 시작되지 않을 때

```bash
# 로그 확인
docker compose -f docker/docker-compose.yml logs [service-name]

# 컨테이너 상태 확인
docker compose -f docker/docker-compose.yml ps

# 재시작
docker compose -f docker/docker-compose.yml restart [service-name]

# 특정 스택만 재시작
docker compose -f docker/docker-compose.serving.yml restart vllm-server
```

### GPU가 인식되지 않을 때

```bash
# NVIDIA Docker Runtime 확인
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# docker-compose.yml에서 GPU 설정 확인
```

### 로그가 수집되지 않을 때

```bash
# Alloy 상태 확인
docker compose -f docker/docker-compose.monitoring.yml logs alloy

# Alloy UI에서 파이프라인 확인
open http://localhost:12345

# 로그 파일 권한 확인
ls -la logs/

# Loki 연결 확인
curl http://localhost:3100/ready

# Alloy 설정 파일 확인
cat deployment/monitoring/configs/alloy/config.alloy
```

### 디스크 공간 부족

```bash
# 오래된 로그 정리
find logs/ -name "*.log" -mtime +7 -delete

# Docker 볼륨 정리
docker system prune -a --volumes

# Loki 데이터 정리 (보관 기간 설정)
# deployment/monitoring/configs/loki/loki-config.yaml 수정

# Prometheus 데이터 정리
# deployment/monitoring/configs/prometheus/prometheus.yml 수정
# retention.time, retention.size 조정
```

## 성능 튜닝

### vLLM 최적화

```yaml
# docker/docker-compose.serving.yml
environment:
  GPU_MEMORY_UTILIZATION: 0.9  # GPU 메모리 사용률 조정
  MAX_MODEL_LEN: 4096          # 최대 시퀀스 길이
  TENSOR_PARALLEL_SIZE: 1      # 멀티 GPU 병렬 처리
```

### Prometheus 데이터 보관 기간

```yaml
# deployment/monitoring/configs/prometheus/prometheus.yml
storage:
  tsdb:
    retention.time: 15d          # 15일간 보관
    retention.size: 50GB         # 최대 50GB
```

### Loki 로그 보관 기간

```yaml
# deployment/monitoring/configs/loki/loki-config.yaml
limits_config:
  retention_period: 168h         # 7일간 보관
```

### Alloy 리소스 제한

```yaml
# docker/docker-compose.monitoring.yml
deploy:
  resources:
    limits:
      memory: 512M
      cpus: '1'
```

## 보안 고려사항

1. **인증 설정**
   - Grafana 기본 비밀번호 변경
   - MinIO 접근 키 변경
   - PostgreSQL 비밀번호 변경

2. **네트워크 격리**
   - 프로덕션에서는 외부 포트 노출 최소화
   - 리버스 프록시 사용 (nginx, traefik)

3. **로그 암호화**
   - 민감한 정보 마스킹
   - TLS/SSL 설정

## 확장성

### 수평 확장

```bash
# vLLM 서버 스케일 아웃
docker compose -f docker/docker-compose.serving.yml up -d --scale vllm-server=3

# FastAPI 서버 스케일 아웃
docker compose -f docker/docker-compose.serving.yml up -d --scale fastapi-server=3
```

### 멀티 노드 배포

Docker Swarm 또는 Kubernetes로 확장 가능:
- 각 서비스를 독립 노드에 배포
- 로드 밸런서 추가 (nginx, traefik)
- 분산 스토리지 사용 (NFS, GlusterFS)
- Alloy를 각 노드에 배포하여 중앙 Loki/Prometheus로 전송

## 참고 자료

### 공식 문서
- [Grafana Alloy Documentation](https://grafana.com/docs/alloy/latest/)
- [Loki Documentation](https://grafana.com/docs/loki/latest/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/grafana/latest/)
- [vLLM Documentation](https://vllm.readthedocs.io/)
- [MLflow Documentation](https://mlflow.org/docs/latest/)

### 프로젝트 문서
- [deployment/CLAUDE.md](CLAUDE.md) - 배포 및 모니터링 가이드
- [GRAFANA_DRILLDOWN_WORKFLOW.md](../docs/references/GRAFANA_DRILLDOWN_WORKFLOW.md) - 대시보드 드릴다운 워크플로우
- [LOGGING.md](../docs/references/LOGGING.md) - 구조화된 로깅 가이드
- [VLLM.md](../docs/references/VLLM.md) - vLLM 서빙 가이드

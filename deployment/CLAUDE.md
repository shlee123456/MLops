# deployment/ - 배포 및 모니터링

> **상위 문서**: [루트 CLAUDE.md](../CLAUDE.md) 참조  
> **사용자 가이드**: [deployment/README.md](README.md) - 상세 배포 가이드

Docker 컨테이너화 + 모니터링 스택 (스택별 분리)

## 구조

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
        ├── prometheus/prometheus.yml
        └── promtail/                # (deprecated - alloy로 대체)
```

## Docker Compose 파일 (docker/ 디렉토리)

```
docker/
├── docker-compose.yml              # 전체 스택 (include)
├── docker-compose.mlflow.yml       # MLflow Stack
├── docker-compose.serving.yml      # Serving Stack
├── docker-compose.monitoring.yml   # Monitoring Stack
└── .env.example                    # 환경변수 템플릿
```

## 서비스 포트

| 포트 (기본값) | 서비스 | 계정 | 환경변수 |
|--------------|--------|------|----------|
| 5050 | MLflow UI | - | `MLFLOW_PORT` |
| 8000 | vLLM (OpenAI API) | - | `VLLM_PORT` |
| 8080 | FastAPI | - | `FASTAPI_EXTERNAL_PORT` |
| 9090 | Prometheus | - | `PROMETHEUS_PORT` |
| 3000 | Grafana | admin/admin | `GRAFANA_PORT` |
| 3100 | Loki | - | `LOKI_PORT` |
| 12345 | Alloy UI | - | `ALLOY_PORT` |
| 9000 | MinIO | minio/minio123 | `MINIO_PORT` |
| 9001 | MinIO Console | minio/minio123 | `MINIO_CONSOLE_PORT` |
| 5432 | PostgreSQL | mlflow/mlflow | `POSTGRES_PORT` |

**포트 변경 방법**: 프로젝트 루트의 `.env` 파일에서 환경변수를 수정하여 포트를 변경할 수 있습니다.

```bash
# 환경 파일 생성
cp env.example .env

# 포트 커스터마이징
vim .env

# 예시
GRAFANA_PORT=3001
MLFLOW_PORT=5051
FASTAPI_EXTERNAL_PORT=8081
```

## 실행

```bash
# 전체 스택
docker compose -f docker/docker-compose.yml up -d

# 개별 스택 실행
docker compose -f docker/docker-compose.mlflow.yml up -d
docker compose -f docker/docker-compose.serving.yml up -d
docker compose -f docker/docker-compose.monitoring.yml up -d

# 스택 조합 실행
docker compose -f docker/docker-compose.mlflow.yml -f docker/docker-compose.serving.yml up -d

# 로그 확인
docker compose -f docker/docker-compose.serving.yml logs -f vllm-server

# 중지
docker compose -f docker/docker-compose.yml down
```

## 서비스 그룹

```
MLflow Stack    : postgres, minio, mlflow-server
Model Serving   : vllm-server, fastapi-server
Monitoring      : loki, prometheus, grafana, alloy
```

> **Note**: Alloy가 node-exporter, cadvisor, promtail 기능을 통합

## Grafana 대시보드

| 파일 | 용도 |
|------|------|
| `system-overview.json` | CPU, 메모리, 디스크 |
| `training-metrics.json` | 학습 loss, 진행률 |
| `inference-metrics.json` | 추론 latency, throughput |
| `inference-detail.json` | 엔드포인트/모델별 상세 분석 |
| `training-detail.json` | 실험별 상세 분석 |
| `logs-dashboard.json` | Loki 로그 뷰어 |

> **드릴다운 워크플로우**: [GRAFANA_DRILLDOWN_WORKFLOW.md](../docs/references/GRAFANA_DRILLDOWN_WORKFLOW.md) 참조

## GPU 서비스 요구사항

### GPU 설정

시스템 GPU 구성:
- **GPU 0**: RTX 5090 (32GB VRAM) - 프로덕션 서빙 권장
- **GPU 1**: RTX 5060 Ti (16GB VRAM) - 테스트/개발 권장

### GPU 번호 지정 방법

특정 GPU를 지정하여 vLLM 서버를 실행할 수 있습니다.

**환경변수 설정:**

```bash
# .env 파일에 추가
GPU_DEVICE_ID=0  # 0: RTX 5090, 1: RTX 5060 Ti
```

**사용 예시:**

```bash
# GPU 0 (RTX 5090) 사용 - 프로덕션
GPU_DEVICE_ID=0 docker compose -f docker/docker-compose.serving.yml up -d

# GPU 1 (RTX 5060 Ti) 사용 - 테스트
GPU_DEVICE_ID=1 docker compose -f docker/docker-compose.serving.yml up -d

# 학습과 서빙 분리
# 터미널 1: GPU 0에서 서빙
GPU_DEVICE_ID=0 docker compose -f docker/docker-compose.serving.yml up -d

# 터미널 2: GPU 1에서 학습
CUDA_VISIBLE_DEVICES=1 python src/train/01_lora_finetune.py
```

**GPU 할당 확인:**

```bash
# GPU 할당 상태 확인 스크립트
./scripts/check_gpu_allocation.sh

# 또는 수동 확인
docker inspect mlops-vllm | jq '.[0].HostConfig.DeviceRequests'
nvidia-smi
```

**Docker Compose 설정:**

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          device_ids: ['${GPU_DEVICE_ID:-0}']
          capabilities: [gpu]
```

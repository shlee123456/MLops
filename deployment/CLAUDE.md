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
| 8000 | vLLM 모델 1 (GPU 0) | - | `MODEL_1_PORT` |
| 8001 | vLLM 모델 2 (GPU 1) | - | `MODEL_2_PORT` |
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

### GPU 구성

시스템 GPU:
- **GPU 0**: RTX 5090 (32GB VRAM) - 대용량 모델/프로덕션 권장
- **GPU 1**: RTX 5060 Ti (16GB VRAM) - 소형 모델/테스트 권장

### 다중 모델 GPU 할당

vLLM 컨테이너는 `.env` 파일의 설정에 따라 **여러 모델을 각각 다른 GPU**에서 실행합니다.

**.env 설정:**

```bash
# =============================================================================
# vLLM 다중 모델 설정
# =============================================================================
# 모델 1 (GPU 0: RTX 5090, 32GB)
MODEL_1_ENABLED=true
MODEL_1_PATH=/models/base/2shlee/llama3-8b-ko-chat-v1
MODEL_1_GPU=0
MODEL_1_PORT=8000
MODEL_1_GPU_MEMORY=0.9
MODEL_1_MAX_LEN=4096

# 모델 2 (GPU 1: RTX 5060 Ti, 16GB)
MODEL_2_ENABLED=true
MODEL_2_PATH=/models/base/meta-llama/Meta-Llama-3-8B-Instruct
MODEL_2_GPU=1
MODEL_2_PORT=8001
MODEL_2_GPU_MEMORY=0.9
MODEL_2_MAX_LEN=4096
```

**실행:**

```bash
# .env 파일 설정 후 단순 실행 (GPU 자동 할당)
docker compose -f docker/docker-compose.serving.yml up -d

# 로그 확인
docker compose -f docker/docker-compose.serving.yml logs -f vllm-server
```

**설정 옵션:**

| 환경변수 | 설명 | 기본값 |
|---------|------|--------|
| `MODEL_N_ENABLED` | 모델 활성화 여부 | `false` |
| `MODEL_N_PATH` | 모델 경로 (컨테이너 내부) | - |
| `MODEL_N_GPU` | GPU 번호 (0 또는 1) | - |
| `MODEL_N_PORT` | API 포트 | 8000, 8001 |
| `MODEL_N_GPU_MEMORY` | GPU 메모리 사용률 | `0.9` |
| `MODEL_N_MAX_LEN` | 최대 시퀀스 길이 | `4096` |

**사용 시나리오:**

```bash
# 시나리오 1: 단일 모델 (GPU 0만 사용)
MODEL_1_ENABLED=true
MODEL_2_ENABLED=false

# 시나리오 2: 두 모델 동시 서빙
MODEL_1_ENABLED=true   # GPU 0 → :8000
MODEL_2_ENABLED=true   # GPU 1 → :8001

# 시나리오 3: GPU 1에서만 서빙 (GPU 0은 학습용)
MODEL_1_ENABLED=false
MODEL_2_ENABLED=true
```

**API 접근:**

```bash
# 모델 1 (GPU 0)
curl http://localhost:8000/v1/models

# 모델 2 (GPU 1)
curl http://localhost:8001/v1/models
```

**GPU 할당 확인:**

```bash
# GPU 할당 상태 확인 스크립트
./scripts/check_gpu_allocation.sh

# nvidia-smi로 프로세스 확인
nvidia-smi
```

### 로깅 설정

vLLM 서비스는 `logs/vllm/` 디렉토리에 파일 로그를 생성합니다.

**로그 파일 경로:**
- 모델 1: `/logs/model1_YYYYMMDD_HHMMSS.log`
- 모델 2: `/logs/model2_YYYYMMDD_HHMMSS.log`

**로그 내용:**
- vLLM 서버 시작 메시지
- 모델 로딩 진행 상황
- API 요청/응답 로그
- 에러 메시지

**로그 확인:**
```bash
# 컨테이너 실행 후 호스트에서 확인
ls -lh logs/vllm/

# 실시간 로그 확인
tail -f logs/vllm/model1_*.log

# Docker 컨테이너 로그 (stdout/stderr)
docker compose -f docker/docker-compose.serving.yml logs -f vllm-server
```

**구현 세부사항:**
- `start-vllm.sh` 스크립트가 각 모델의 출력을 타임스탬프가 포함된 로그 파일로 리다이렉트
- `tee` 명령으로 콘솔과 파일에 동시 출력
- 모델별 접두사 (`[Model1]`, `[Model2]`)로 구분

### 아키텍처

```
                    ┌─────────────────────────────────────┐
                    │         vLLM Container              │
                    │         (mlops-vllm)                │
                    │                                     │
                    │  ┌─────────────┐ ┌─────────────┐   │
                    │  │  Model 1    │ │  Model 2    │   │
                    │  │  GPU 0      │ │  GPU 1      │   │
                    │  │  :8000      │ │  :8001      │   │
                    │  └─────────────┘ └─────────────┘   │
                    │                                     │
                    │  start-vllm.sh (프로세스 관리)      │
                    └─────────────────────────────────────┘
                              ↓              ↓
                    ┌─────────────┐ ┌─────────────┐
                    │   GPU 0     │ │   GPU 1     │
                    │  RTX 5090   │ │ RTX 5060 Ti │
                    │   32GB      │ │    16GB     │
                    └─────────────┘ └─────────────┘
```

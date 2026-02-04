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

#### vLLM 서비스 로깅

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

#### FastAPI 서비스 로깅

FastAPI 서비스는 `logs/fastapi/` 디렉토리에 구조화된 JSON 로그를 생성합니다.

**로그 파일 경로:**
- 파일: `/logs/app.log` (호스트: `logs/fastapi/app.log`)
- 포맷: JSON Lines (각 줄이 하나의 JSON 객체)
- 로테이션: 10MB 단위, 최대 5개 백업

**로그 내용:**
- 애플리케이션 시작/종료 이벤트
- HTTP 요청/응답 (method, path, status_code, duration_ms)
- Request ID 추적 (X-Request-ID 헤더)
- 에러 및 예외 스택 트레이스

**로그 필드:**
```json
{
  "event": "request_completed",
  "level": "info",
  "logger": "http",
  "timestamp": "2026-01-27T15:46:41.479516Z",
  "request_id": "3b64dae4",
  "method": "GET",
  "path": "/docs",
  "status_code": 200,
  "duration_ms": 1.2,
  "service": "fastapi",
  "app_name": "MLOps Chatbot API"
}
```

**로그 확인:**
```bash
# 파일 로그 확인 (JSON 형식)
tail -f logs/fastapi/app.log | jq .

# Docker 컨테이너 로그 (stdout)
docker compose -f docker/docker-compose.serving.yml logs -f fastapi-server

# 특정 request_id 검색
grep "3b64dae4" logs/fastapi/app.log | jq .

# 에러만 필터링
jq 'select(.level=="error")' logs/fastapi/app.log
```

**환경변수 설정:**
FastAPI 컨테이너의 `LOG_DIR` 환경변수가 `/logs`로 설정되어야 파일 로그가 생성됩니다.

```yaml
# docker-compose.serving.yml
environment:
  LOG_DIR: /logs  # 필수!
volumes:
  - ../logs/fastapi:/logs
```

**구현 세부사항:**
- `src/serve/core/logging.py`의 structlog 기반 로깅 시스템
- `RequestLoggingMiddleware`가 모든 HTTP 요청을 자동 로깅
- `/health`, `/metrics` 엔드포인트는 로깅에서 제외
- JSON 로그는 파일에만 기록, 콘솔은 개발 모드에서 컬러 출력

#### MLflow 서비스 로깅

MLflow 서비스는 `logs/mlflow/` 디렉토리에 로그 파일을 생성합니다.

**로그 파일 경로:**
- 파일: `/logs/mlflow_YYYYMMDD_HHMMSS.log` (호스트: `logs/mlflow/mlflow_*.log`)
- 포맷: 텍스트 (gunicorn 기본 로그 형식)

**로그 내용:**
- MLflow 서버 시작 메시지 (gunicorn)
- Worker 프로세스 초기화
- 서버 바인딩 정보
- 에러 및 예외 메시지

**로그 예시:**
```
[2026-01-27 15:50:54 +0000] [77] [INFO] Starting gunicorn 21.2.0
[2026-01-27 15:50:54 +0000] [77] [INFO] Listening at: http://0.0.0.0:5000 (77)
[2026-01-27 15:50:54 +0000] [77] [INFO] Using worker: sync
[2026-01-27 15:50:54 +0000] [78] [INFO] Booting worker with pid: 78
```

**로그 확인:**
```bash
# 파일 로그 확인
tail -f logs/mlflow/mlflow_*.log

# Docker 컨테이너 로그 (stdout)
docker compose -f docker/docker-compose.mlflow.yml logs -f mlflow-server

# 로그 파일 목록
ls -lh logs/mlflow/
```

**구현 세부사항:**
- `start-mlflow.sh` 엔트리포인트 스크립트가 MLflow 서버의 출력을 타임스탬프가 포함된 로그 파일로 리다이렉트
- `tee` 명령으로 콘솔과 파일에 동시 출력
- Docker Compose에서 `../logs/mlflow:/logs` 볼륨 마운트 설정
- Dockerfile에서 `/logs` 디렉토리 사전 생성

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

## 로그 수집 트러블슈팅

이 섹션은 Alloy-Loki 로그 수집 문제 해결 과정에서 발견한 이슈와 해결 방법을 문서화합니다.

### 문제 1: FastAPI JSON 로그가 Loki에 저장되지 않음

**증상:**
- Alloy가 FastAPI 로그 파일을 읽고 있음 (Alloy 로그에 "tail routine: started" 메시지 확인)
- Loki API 쿼리 시 데이터 없음 (`total_entries=0`)

**원인:**
FastAPI는 structlog를 사용하여 JSON 로그를 생성하는데, 메시지를 `"event"` 필드에 저장합니다. 하지만 Alloy 설정이 `"message"` 필드만 추출하려고 해서 매칭 실패:

```json
// FastAPI 로그 형식
{"event": "request_completed", "level": "info", "timestamp": "..."}

// Alloy의 기존 설정 (실패)
stage.json {
  expressions = {
    message = "message"  // "event" 필드 누락!
  }
}
```

**해결 방법:**
`stage.template`을 사용하여 `event` 또는 `message` 필드 중 존재하는 것을 output으로 매핑:

```alloy
loki.process "json_logs" {
  stage.json {
    expressions = {
      level     = "level",
      event     = "event",
      message   = "message",
      logger    = "logger",
      timestamp = "timestamp",
    }
  }

  // Extract message from either "event" or "message" field
  stage.template {
    source   = "output"
    template = "{{ if .event }}{{ .event }}{{ else }}{{ .message }}{{ end }}"
  }

  stage.labels {
    values = {
      level = "",
    }
  }
  stage.timestamp {
    source = "timestamp"
    format = "RFC3339"
  }
  forward_to = [loki.write.default.receiver]
}
```

**검증:**
```bash
# Loki API로 로그 조회
curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={job="fastapi"}' \
  --data-urlencode 'limit=5' | jq -r '.data.result[0].values[][1]'
```

### 문제 2: Loki 연결 자체가 문제인지 JSON 파싱이 문제인지 불명확

**증상:**
- JSON 로그가 수집되지 않음
- Loki와 Alloy 간 연결 상태 불확실

**해결 방법:**
JSON 파싱을 우회한 plaintext 로그 소스를 추가하여 기본 연결 검증:

```alloy
loki.source.file "test_plaintext" {
  targets = [
    {__path__ = "/logs/test/plaintext.log", job = "test", service = "test"},
  ]
  forward_to = [loki.write.default.receiver]  // JSON 파싱 우회
}
```

테스트 로그 생성 및 검증:
```bash
# 테스트 로그 생성
mkdir -p logs/test
for i in {1..10}; do echo "Test log entry $i" >> logs/test/plaintext.log; done

# Alloy 재시작
docker restart mlops-alloy

# Loki에서 조회
curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={job="test"}' \
  --data-urlencode 'limit=10'
```

**결과:** Loki 연결 자체는 정상 작동, 문제는 JSON 파싱에 있었음.

### 문제 3: Docker stdout 로그 수집 작동 확인

**요구사항:**
- 파일 기반 로그 대신 Docker stdout 로그를 직접 수집
- 컨테이너 자동 발견
- 볼륨 마운트 없이 로그 수집

**설정:**
Alloy는 Docker API를 통해 컨테이너를 자동 발견하고 stdout/stderr을 수집합니다:

```alloy
discovery.docker "containers" {
  host = "unix:///var/run/docker.sock"
  refresh_interval = "5s"
  filter {
    name   = "label"
    values = ["com.docker.compose.project=docker"]
  }
}

discovery.relabel "docker_logs" {
  targets = discovery.docker.containers.targets

  // Drop monitoring stack logs
  rule {
    source_labels = ["__meta_docker_container_name"]
    regex         = "/mlops-(loki|alloy|prometheus|grafana)"
    action        = "drop"
  }

  // Extract container name as label
  rule {
    source_labels = ["__meta_docker_container_name"]
    regex         = "/mlops-(.*)"
    target_label  = "container"
  }
}

loki.source.docker "docker_logs" {
  host       = "unix:///var/run/docker.sock"
  targets    = discovery.relabel.docker_logs.output
  forward_to = [loki.process.docker_json.receiver]
}
```

**검증:**
```bash
# Docker 로그 조회 (container 레이블)
curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={container="fastapi"}' \
  --data-urlencode 'limit=5'

# 또는 compose_service 레이블
curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={compose_service="fastapi-server"}' \
  --data-urlencode 'limit=5'
```

**파일 기반 vs Docker stdout 비교:**

| 방식 | 레이블 쿼리 | 장점 | 단점 | 사용 환경 |
|------|------------|------|------|----------|
| **파일 기반** | `{job="fastapi"}` | 영구 저장, 컨테이너 재시작 시에도 유지, 로그 파일 직접 접근 가능 | 볼륨 마운트 필요, 로그 파일 관리 필요 | 프로덕션 |
| **Docker stdout** | `{container="fastapi"}` | 자동 발견, 볼륨 마운트 불필요, 컨테이너 시작 즉시 수집 | 컨테이너 재시작 시 이전 로그 소실 | 개발/디버깅 |

**권장사항:** 두 방식 모두 유지 (각각 다른 레이블로 구분됨)

### 문제 4: MLflow 로그 파일 경로 불일치

**증상:**
- Alloy 로그에 "stat failed" 에러: `stat /logs/mlflow/mlflow.log: no such file or directory`
- MLflow 로그가 Loki에 수집되지 않음

**원인:**
MLflow 컨테이너의 `start-mlflow.sh` 스크립트가 타임스탬프가 포함된 파일명으로 로그를 생성:
```
/logs/mlflow_20260204_034407.log
```

하지만 Alloy 설정은 고정된 파일명을 기대:
```alloy
{__path__ = "/logs/mlflow/mlflow.log", ...}
```

**해결 방법 1: 심볼릭 링크 (권장)**
MLflow 컨테이너 내부에서 심볼릭 링크 생성:
```bash
docker exec mlops-mlflow sh -c "cd /logs && ln -sf mlflow_20260204_034407.log mlflow.log"
```

**해결 방법 2: Alloy 설정에서 와일드카드 사용 (실패)**
Alloy의 `loki.source.file`은 glob 패턴을 지원하지만, 파일이 존재해야 합니다. 와일드카드를 stat으로 직접 사용하면 실패:
```alloy
// 작동하지 않음
{__path__ = "/logs/mlflow/mlflow*.log", ...}  // stat failed 에러
```

**권장 사항:**
- MLflow 컨테이너의 엔트리포인트 스크립트에서 자동으로 심볼릭 링크 생성
- 또는 로그 파일명을 고정 (`mlflow.log`)

### 문제 5: Plaintext 로그가 JSON 파싱 파이프라인을 거치면서 버려짐

**증상:**
- MLflow와 vLLM 로그 (plaintext 형식)가 Loki에 저장되지 않음
- Alloy 로그에 파싱 에러 없음

**원인:**
Plaintext 로그가 JSON 파싱 파이프라인(`loki.process.json_logs`)을 거치면서 JSON이 아니므로 버려짐

**해결 방법:**
Plaintext 로그는 JSON 파싱을 우회하고 직접 `loki.write.default.receiver`로 전송:

```alloy
// MLflow logs (plaintext)
loki.source.file "mlflow" {
  targets = [
    {__path__ = "/logs/mlflow/mlflow.log", job = "mlflow", service = "mlops", log_type = "mlflow"},
  ]
  forward_to = [loki.write.default.receiver]  // JSON 파싱 우회
}

// vLLM logs (plaintext)
loki.source.file "vllm_model1" {
  targets = [
    {__path__ = "/logs/vllm/model1*.log", job = "vllm", service = "mlops", log_type = "vllm", model = "model1"},
  ]
  forward_to = [loki.write.default.receiver]  // JSON 파싱 우회
}
```

### Alloy 설정 검증 방법

#### 1. Alloy 로그 확인

Alloy 컨테이너 로그에서 로그 수집 상태 확인:
```bash
# 전체 로그 확인
docker logs mlops-alloy --tail 50

# 특정 소스 확인
docker logs mlops-alloy 2>&1 | grep "loki.source.file.fastapi"

# 에러만 필터링
docker logs mlops-alloy 2>&1 | grep -E "(error|warn|fail)" -i
```

**정상 작동 시 로그:**
```
level=info msg="tail routine: started" component_id=loki.source.file.fastapi path=/logs/fastapi/app.log
level=info msg="Seeked /logs/fastapi/app.log - &{Offset:24907 Whence:0}"
```

**문제 발생 시 로그:**
```
level=error msg="failed to tail file, stat failed" component_id=loki.source.file.mlflow error="stat /logs/mlflow/mlflow.log: no such file or directory"
```

#### 2. Loki API 테스트

##### 레이블 확인
Loki에 수집된 레이블 확인:
```bash
# 모든 레이블
curl -s 'http://localhost:3100/loki/api/v1/labels' | jq .

# 특정 레이블의 값
curl -s 'http://localhost:3100/loki/api/v1/label/job/values' | jq .
```

##### 로그 조회 (instant query)
최신 로그 조회:
```bash
# FastAPI 로그
curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={job="fastapi"}' \
  --data-urlencode 'limit=5' | jq .

# MLflow 로그
curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={job="mlflow"}' \
  --data-urlencode 'limit=5' | jq .

# Docker stdout 로그
curl -G -s 'http://localhost:3100/loki/api/v1/query' \
  --data-urlencode 'query={container="fastapi"}' \
  --data-urlencode 'limit=5' | jq .
```

##### 로그 조회 (range query)
특정 시간 범위의 로그 조회:
```bash
curl -G -s 'http://localhost:3100/loki/api/v1/query_range' \
  --data-urlencode 'query={job="fastapi"}' \
  --data-urlencode 'limit=100' \
  --data-urlencode "start=$(date -d '10 minutes ago' +%s)000000000" \
  --data-urlencode "end=$(date +%s)000000000" | jq .
```

#### 3. Alloy HTTP API

Alloy의 컴포넌트 상태 확인:
```bash
# Alloy 상태
curl -s 'http://localhost:12345/-/ready'

# Discovery 타겟 확인
curl -s 'http://localhost:12345/api/v0/web/components/discovery.docker.containers' | jq .

# loki.write 상태
curl -s 'http://localhost:12345/api/v0/web/components/loki.write.default' | jq '.health'
```

#### 4. 로그 파일 확인

Alloy 컨테이너 내부에서 로그 파일 확인:
```bash
# 파일 존재 확인
docker exec mlops-alloy ls -lh /logs/fastapi/ /logs/mlflow/

# 파일 내용 확인
docker exec mlops-alloy tail /logs/fastapi/app.log
```

### Grafana 로그 쿼리 예시

Grafana Explore 메뉴에서 사용할 수 있는 LogQL 쿼리 예시:

#### 기본 쿼리

```logql
# FastAPI 로그 (파일 기반)
{job="fastapi"}

# FastAPI 로그 (Docker stdout)
{container="fastapi"}

# MLflow 로그
{job="mlflow"}

# vLLM 로그
{job="vllm"}
```

#### 레이블 필터

```logql
# 특정 로그 레벨만
{job="fastapi", level="error"}

# 특정 서비스
{service="mlops", log_type="api"}

# Compose 서비스명으로
{compose_service="fastapi-server"}
```

#### 로그 내용 필터 (라인 필터)

```logql
# "error" 문자열 포함
{job="fastapi"} |= "error"

# "error" 제외
{job="fastapi"} != "error"

# 정규표현식 매칭
{job="fastapi"} |~ "status_code\":5.."

# POST 요청만
{job="fastapi"} |= "POST"
```

#### JSON 필드 추출

```logql
# status_code 필드 추출
{job="fastapi"} | json | status_code > 400

# duration_ms 평균
avg_over_time({job="fastapi"} | json | unwrap duration_ms [5m])

# request_id로 그룹화
sum by(request_id) (count_over_time({job="fastapi"} | json [5m]))
```

#### 시계열 쿼리

```logql
# 분당 요청 수
rate({job="fastapi"}[1m])

# 에러 비율
sum(rate({job="fastapi", level="error"}[5m])) / sum(rate({job="fastapi"}[5m]))

# 95 percentile 응답 시간
histogram_quantile(0.95, sum(rate({job="fastapi"} | json | unwrap duration_ms [5m])) by (le))
```

### 트러블슈팅 체크리스트

로그 수집이 작동하지 않을 때 다음 순서로 확인:

1. **서비스 실행 확인**
   ```bash
   docker ps | grep -E "loki|alloy|fastapi|mlflow"
   ```

2. **로그 파일 생성 확인**
   ```bash
   ls -lh logs/fastapi/ logs/mlflow/ logs/vllm/
   ```

3. **Alloy 로그 확인**
   ```bash
   docker logs mlops-alloy --tail 50 | grep -E "(error|tail routine)" -i
   ```

4. **Loki 연결 확인**
   ```bash
   curl -s 'http://localhost:3100/ready'
   ```

5. **Loki 레이블 확인**
   ```bash
   curl -s 'http://localhost:3100/loki/api/v1/labels' | jq .
   ```

6. **Loki 데이터 확인**
   ```bash
   curl -G -s 'http://localhost:3100/loki/api/v1/query' \
     --data-urlencode 'query={job="fastapi"}' \
     --data-urlencode 'limit=1' | jq .
   ```

7. **Alloy 재시작 (필요 시)**
   ```bash
   docker restart mlops-alloy
   sleep 10
   # 다시 6번 확인
   ```

8. **Loki와 Alloy 함께 재시작 (최후의 수단)**
   ```bash
   docker restart mlops-loki mlops-alloy
   sleep 15
   # 새 로그 생성
   curl -s http://localhost:8080/health
   sleep 5
   # 다시 6번 확인
   ```

### 최종 작동하는 Alloy 설정 요약

**JSON 로그 (FastAPI):**
- `loki.source.file` → `loki.process.json_logs` → `loki.write.default`
- `stage.template`로 `event` 또는 `message` 필드 처리
- Docker stdout 로그도 동일한 파이프라인 사용

**Plaintext 로그 (MLflow, vLLM):**
- `loki.source.file` → `loki.write.default` (JSON 파싱 우회)
- 타임스탬프가 포함된 파일명은 심볼릭 링크 사용

**Docker stdout 로그:**
- `discovery.docker` → `discovery.relabel` → `loki.source.docker` → `loki.process.docker_json` → `loki.write.default`
- 컨테이너 레이블 자동 추출: `container`, `compose_service`, `compose_project`

**주요 설정 포인트:**
- JSON 파싱은 로그 형식에 따라 선택적으로 사용
- Plaintext 로그는 파싱 우회
- Docker 로그와 파일 로그 모두 사용 가능 (각각 다른 레이블)
- Alloy 재시작 시 새 로그만 수집 (EOF에서 tailing 시작)
- Loki는 개발 환경에서 재시작 시 데이터 초기화 (프로덕션에서는 retention 설정 필요)

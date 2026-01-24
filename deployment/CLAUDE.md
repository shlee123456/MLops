# deployment/ - 배포 및 모니터링

> **상위 문서**: [루트 CLAUDE.md](../CLAUDE.md) 참조

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

| 포트 | 서비스 | 계정 |
|------|--------|------|
| 5050 | MLflow UI | - |
| 8000 | vLLM (OpenAI API) | - |
| 8080 | FastAPI | - |
| 9090 | Prometheus | - |
| 3000 | Grafana | admin/admin |
| 3100 | Loki | - |
| 12345 | Alloy UI | - |
| 9000 | MinIO | minio/minio123 |
| 9001 | MinIO Console | minio/minio123 |
| 5432 | PostgreSQL | mlflow/mlflow |

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

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

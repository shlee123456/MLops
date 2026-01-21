# deployment/ - 배포 및 모니터링

> **상위 문서**: [루트 CLAUDE.md](../CLAUDE.md) 참조

Docker 컨테이너화 + 모니터링 스택

## 구조

```
deployment/
├── docker/
│   ├── Dockerfile.fastapi
│   ├── Dockerfile.mlflow
│   ├── Dockerfile.serve     # vLLM
│   └── Dockerfile.train
└── configs/
    ├── prometheus/prometheus.yml
    ├── grafana/dashboards/
    ├── loki/loki-config.yaml
    ├── alloy/config.alloy       # 통합 에이전트 (logs + metrics)
    └── promtail/                # (deprecated - alloy로 대체)
```

## 서비스 포트

| 포트 | 서비스 | 계정 |
|------|--------|------|
| 5000 | MLflow UI | - |
| 8000 | vLLM (OpenAI API) | - |
| 8080 | FastAPI | - |
| 9090 | Prometheus | - |
| 3000 | Grafana | admin/admin |
| 3100 | Loki | - |
| 12345 | Alloy UI | - |
| 9000 | MinIO | minio/minio123 |
| 9001 | MinIO Console | minio/minio123 |
| 5432 | PostgreSQL | mlflow/mlflow |

## 실행 (docker-compose.yml은 프로젝트 루트에 위치)

```bash
# 전체 스택
docker-compose up -d

# 특정 서비스
docker-compose up -d mlflow-server grafana

# 로그 확인
docker-compose logs -f vllm-server

# 중지
docker-compose down
```

## 서비스 그룹

```
MLflow Stack    : postgres, minio, mlflow-server
Model Serving   : vllm-server, fastapi-server
Monitoring      : prometheus, grafana, alloy
Logging         : loki (alloy가 로그 수집)
```

> **Note**: Alloy가 node-exporter, cadvisor, promtail 기능을 통합

## Grafana 대시보드

| 파일 | 용도 |
|------|------|
| `system-overview.json` | CPU, 메모리, 디스크 |
| `training-metrics.json` | 학습 loss, 진행률 |
| `inference-metrics.json` | 추론 latency, throughput |
| `logs-dashboard.json` | Loki 로그 뷰어 |

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

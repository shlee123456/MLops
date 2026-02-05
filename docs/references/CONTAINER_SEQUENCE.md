# 컨테이너 실행 시퀀스 가이드

> MLOps 프로젝트의 Docker 컨테이너 시작 순서 및 의존성 관계

## 📊 전체 아키텍처 구조

```
mlops-network (공유 네트워크)
├── MLflow Stack       (실험 추적)
├── Serving Stack      (AI 모델 서빙)
└── Monitoring Stack   (로그 & 메트릭)
```

---

## 🔄 실행 시퀀스 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│ 1단계: 기반 인프라 시작 (병렬)                                 │
└─────────────────────────────────────────────────────────────┘
  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
  │  postgres    │  │    minio     │  │     loki     │
  │  (MLflow)    │  │  (MLflow)    │  │ (Monitoring) │
  │              │  │              │  │              │
  │ Port: 5432   │  │ Port: 9000   │  │ Port: 3100   │
  │ Health: 10s  │  │ Health: 30s  │  │ Health: 10s  │
  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
         │                 │                 │
         ✅ Healthy        ✅ Healthy        ✅ Healthy

┌─────────────────────────────────────────────────────────────┐
│ 2단계: 의존성 서비스 시작                                       │
└─────────────────────────────────────────────────────────────┘
         │                 │
         └────────┬────────┘
                  ▼
         ┌──────────────┐           ┌──────────────┐
         │ mlflow-server│           │  prometheus  │
         │              │           │ (Monitoring) │
         │ Port: 5050   │           │              │
         │ Health: 30s  │           │ Port: 9090   │
         │              │           │ Health: 10s  │
         │ depends_on:  │           └──────┬───────┘
         │  - postgres  │                  │
         │  - minio     │                  ✅ Healthy
         └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│ 3단계: AI/ML 서빙 시작 (병렬)                                  │
└─────────────────────────────────────────────────────────────┘
         ┌──────────────┐           ┌──────────────┐
         │ vllm-server  │           │fastapi-server│
         │              │           │              │
         │ GPU: 0, 1    │◄──────────│ API Gateway  │
         │ Port: 8000   │  연결      │ Port: 8080   │
         │ Health: 30s  │           │ Health: 30s  │
         │ Start: 120s  │           │              │
         └──────────────┘           └──────────────┘
                                           │
                                           │ API 제공

┌─────────────────────────────────────────────────────────────┐
│ 4단계: 모니터링 통합 (의존성 대기)                              │
└─────────────────────────────────────────────────────────────┘
         ┌──────────────┐           ┌──────────────┐
         │    alloy     │           │   grafana    │
         │              │           │              │
         │ Port: 12345  │           │ Port: 3000   │
         │              │           │              │
         │ depends_on:  │           │ depends_on:  │
         │  - loki      │           │  - prometheus│
         │  - prometheus│           │  - loki      │
         └──────────────┘           └──────────────┘
                │                          │
                └──────────┬───────────────┘
                           ▼
                    ✅ 전체 스택 준비 완료
```

---

## 📋 상세 실행 순서

### Phase 1: 기반 인프라 (0~30초)

| 순서 | 서비스 | 스택 | 포트 | Health Check | 역할 |
|------|--------|------|------|--------------|------|
| 1 | `postgres` | MLflow | 5432 | 10s 간격 | MLflow 백엔드 DB |
| 2 | `minio` | MLflow | 9000, 9001 | 30s 간격 | 아티팩트 스토리지 (S3 호환) |
| 3 | `loki` | Monitoring | 3100 | 10s 간격 | 로그 수집 저장소 |
| 4 | `prometheus` | Monitoring | 9090 | 10s 간격 | 메트릭 수집 |

**Health Check 명령어:**
```bash
# postgres
pg_isready -U mlflow

# minio
curl -f http://localhost:9000/minio/health/live

# loki
wget --no-verbose --tries=1 --spider http://localhost:3100/ready

# prometheus
wget --spider -q http://localhost:9090/-/healthy
```

---

### Phase 2: 의존 서비스 (30~60초)

| 순서 | 서비스 | 의존성 | 포트 | Health Check | 역할 |
|------|--------|--------|------|--------------|------|
| 5 | `mlflow-server` | postgres✅, minio✅ | 5050 | 30s 간격 | 실험 추적 및 모델 레지스트리 |

**의존성 대기:**
```yaml
depends_on:
  postgres:
    condition: service_healthy  # postgres가 healthy 상태일 때까지 대기
  minio:
    condition: service_healthy  # minio가 healthy 상태일 때까지 대기
```

---

### Phase 3: AI 서빙 (60~180초)

| 순서 | 서비스 | 포트 | Start Period | Health Check | 역할 |
|------|--------|------|--------------|--------------|------|
| 6 | `vllm-server` | 8000, 8001 | 120초 | 30s 간격 | LLM 추론 엔진 (GPU 로딩) |
| 7 | `fastapi-server` | 8080 | - | 30s 간격 | REST API 게이트웨이 |

**vLLM 특이사항:**
- `start_period: 120s`: 모델 로딩 시간 고려 (GPU 메모리 할당)
- Health Check는 120초 후부터 시작
- GPU 0, 1을 사용하여 다중 모델 지원 가능

**FastAPI 연결:**
```yaml
environment:
  VLLM_BASE_URL: http://localhost:8000/v1  # vLLM 서버 연결
```

---

### Phase 4: 모니터링 통합 (의존성 충족 후)

| 순서 | 서비스 | 의존성 | 포트 | 역할 |
|------|--------|--------|------|------|
| 8 | `alloy` | loki, prometheus | 12345 | 로그/메트릭 수집 에이전트 |
| 9 | `grafana` | prometheus✅, loki✅ | 3000 | 시각화 대시보드 |

**Grafana 의존성:**
```yaml
depends_on:
  prometheus:
    condition: service_healthy  # 메트릭 소스 준비 대기
  loki:
    condition: service_healthy  # 로그 소스 준비 대기
```

---

## 🔍 핵심 의존성 관계

### MLflow 스택
```
postgres ─┐
          ├─→ mlflow-server
minio ────┘
```

### Monitoring 스택
```
loki ──────┐
           ├─→ alloy
prometheus ┤
           └─→ grafana
```

### Serving 스택 (암묵적 의존성)
```
vllm-server ──→ fastapi-server
    (VLLM_BASE_URL 환경변수로 연결)
```

---

## ⏱️ 예상 시작 시간

| 단계 | 시간 | 누적 |
|------|------|------|
| 기반 인프라 Health | ~30초 | 30초 |
| MLflow 서버 시작 | ~20초 | 50초 |
| Prometheus 준비 | ~10초 | 60초 |
| vLLM 모델 로딩 | ~120초 | 180초 |
| 전체 스택 준비 | +10초 | **~190초 (3분 10초)** |

### Health Check 타임라인

```
0s   ────┬──── postgres (first check)
        │
       10s ──┬── postgres healthy ✅
             │   loki (first check)
             │   prometheus (first check)
        │
       20s ──┬── loki healthy ✅
             │   prometheus healthy ✅
             │   minio (first check)
        │
       30s ──┬── minio healthy ✅
             │   mlflow-server 시작
        │
       50s ──┬── mlflow-server healthy ✅
             │
       60s ──┬── vllm-server 시작 (start_period 시작)
             │   fastapi-server 시작
        │
       90s ──┬── fastapi-server healthy ✅
             │
      180s ──┬── vllm-server (start_period 종료)
             │   vllm-server (first health check)
        │
      210s ──┬── vllm-server healthy ✅
             │   alloy 시작
             │   grafana 시작
        │
      240s ──┴── 전체 스택 준비 완료 ✅
```

---

## 🚀 실행 명령어

### 전체 스택 시작 (권장)
```bash
docker compose -f docker/docker-compose.yml up -d
```

### 개별 스택 시작
```bash
# MLflow 스택만
docker compose -f docker/docker-compose.mlflow.yml up -d

# AI 서빙 스택만
docker compose -f docker/docker-compose.serving.yml up -d

# 모니터링 스택만
docker compose -f docker/docker-compose.monitoring.yml up -d
```

### 상태 확인
```bash
# 전체 상태
docker compose -f docker/docker-compose.yml ps

# 특정 서비스 로그
docker compose -f docker/docker-compose.yml logs -f vllm-server
docker compose -f docker/docker-compose.yml logs -f fastapi-server

# Health Check 상태
docker inspect mlops-vllm | jq '.[0].State.Health'
docker inspect mlops-fastapi | jq '.[0].State.Health'
```

### 순차 시작 (디버깅용)
```bash
# 1. 기반 인프라
docker compose -f docker/docker-compose.mlflow.yml up -d postgres minio
docker compose -f docker/docker-compose.monitoring.yml up -d loki prometheus

# 2. 의존 서비스
sleep 30
docker compose -f docker/docker-compose.mlflow.yml up -d mlflow-server

# 3. AI 서빙
sleep 20
docker compose -f docker/docker-compose.serving.yml up -d vllm-server fastapi-server

# 4. 모니터링 통합
sleep 120
docker compose -f docker/docker-compose.monitoring.yml up -d alloy grafana
```

---

## 🛠️ 트러블슈팅

### vLLM이 시작되지 않을 때
```bash
# GPU 확인
nvidia-smi

# vLLM 로그 확인
docker logs mlops-vllm --tail 100 -f

# 모델 경로 확인
docker exec mlops-vllm ls -la /models/base/meta-llama/
```

### FastAPI가 vLLM에 연결되지 않을 때
```bash
# vLLM Health Check
curl http://localhost:8000/health

# FastAPI 환경변수 확인
docker exec mlops-fastapi env | grep VLLM

# 네트워크 연결 확인
docker exec mlops-fastapi ping vllm-server
```

### MLflow가 시작되지 않을 때
```bash
# Postgres 연결 확인
docker exec mlops-mlflow psql -h postgres -U mlflow -d mlflow -c '\l'

# MinIO 연결 확인
docker exec mlops-mlflow curl http://minio:9000/minio/health/live
```

### Grafana 데이터소스 연결 실패
```bash
# Prometheus 확인
curl http://localhost:9090/-/healthy

# Loki 확인
curl http://localhost:3100/ready

# Grafana 프로비저닝 로그
docker logs mlops-grafana | grep -i provisioning
```

---

## 📊 포트 매핑 요약

| 서비스 | 컨테이너 포트 | 호스트 포트 | 용도 |
|--------|--------------|------------|------|
| postgres | 5432 | 5432 | PostgreSQL DB |
| minio | 9000 | 9000 | MinIO API |
| minio | 9001 | 9001 | MinIO Console |
| mlflow-server | 5000 | 5050 | MLflow UI |
| loki | 3100 | 3100 | Loki API |
| prometheus | 9090 | 9090 | Prometheus UI |
| alloy | 12345 | 12345 | Alloy UI |
| grafana | 3000 | 3000 | Grafana UI |
| vllm-server | 8000 | 8000 | vLLM Model 1 |
| vllm-server | 8001 | 8001 | vLLM Model 2 |
| fastapi-server | 8080 | 8080 | FastAPI |

---

## 📚 관련 문서

- [VLLM.md](./VLLM.md) - vLLM 서빙 상세 가이드
- [LOGGING.md](./LOGGING.md) - 로깅 구조 및 설정
- [deployment/CLAUDE.md](../../deployment/CLAUDE.md) - Docker 배포 설정
- [src/serve/CLAUDE.md](../../src/serve/CLAUDE.md) - FastAPI 서빙 아키텍처

---

## 🔒 보안 고려사항

### 기본 인증 정보 (운영 환경에서 반드시 변경)
```bash
# PostgreSQL
POSTGRES_USER=mlflow
POSTGRES_PASSWORD=mlflow

# MinIO
MINIO_ROOT_USER=minio
MINIO_ROOT_PASSWORD=minio123

# Grafana
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
```

### 환경변수 설정
```bash
# .env 파일 생성
cp env.example .env

# 민감 정보 수정
nano .env
```

---

## 🔄 재시작 순서

### 전체 재시작
```bash
docker compose -f docker/docker-compose.yml restart
```

### 개별 서비스 재시작 (의존성 고려)
```bash
# 1. 기반 서비스 (의존성 있는 서비스 먼저 중단 필요)
docker compose -f docker/docker-compose.yml stop mlflow-server
docker compose -f docker/docker-compose.yml restart postgres
docker compose -f docker/docker-compose.yml start mlflow-server

# 2. AI 서빙 (FastAPI는 vLLM 의존)
docker compose -f docker/docker-compose.yml restart vllm-server
docker compose -f docker/docker-compose.yml restart fastapi-server

# 3. 모니터링 (Grafana는 Prometheus/Loki 의존)
docker compose -f docker/docker-compose.yml stop grafana
docker compose -f docker/docker-compose.yml restart prometheus loki
docker compose -f docker/docker-compose.yml start grafana
```

---

**마지막 업데이트**: 2026-02-05
**문서 버전**: 1.0

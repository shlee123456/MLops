# 세션 히스토리: 모니터링 스택 상태 점검 및 수정

**날짜**: 2026-01-18

## 완료한 작업

### 1. PostgreSQL/MLflow 메트릭 스크랩 job 제거
- **파일**: `deployment/configs/prometheus/prometheus.yml`
- **내용**: PostgreSQL과 MLflow는 기본 `/metrics` 엔드포인트를 제공하지 않아 스크랩 실패 발생
- **조치**: 해당 job을 주석 처리하고 필요시 별도 exporter 추가 필요함을 명시

### 2. FastAPI 로그 경로 수정
- **파일**: `src/serve/core/logging.py`
- **변경**: `./logs/fastapi` → `/logs`
- **이유**: Docker 볼륨 매핑 (`./logs/fastapi:/logs`)과 애플리케이션 로그 경로 일치시킴

### 3. Grafana datasource uid 설정
- **파일**: `deployment/configs/grafana/provisioning/datasources/datasources.yaml`
- **추가**: Prometheus와 Loki datasource에 고정 `uid` 필드 추가
  - Prometheus: `uid: prometheus`
  - Loki: `uid: loki`
- **이유**: 대시보드에서 참조하는 uid와 일치시켜 datasource 연결 오류 방지

### 4. Docker Compose 헬스체크 추가
- **파일**: `docker-compose.yml`
- **추가된 헬스체크**:
  - `mlflow-server`: `curl -f http://localhost:5000/health`
  - `vllm-server`: `curl -f http://localhost:8000/health` (start_period: 120s)
- **의존성 조건 개선**: fastapi-server의 vllm-server 의존성을 `service_healthy`로 변경

## 수정된 파일 목록
1. `deployment/configs/prometheus/prometheus.yml`
2. `src/serve/core/logging.py`
3. `deployment/configs/grafana/provisioning/datasources/datasources.yaml`
4. `docker-compose.yml`

## 다음 세션 TODO
- Docker Compose 스택 재시작 후 Prometheus 타겟 상태 확인
- Grafana 대시보드 로드 검증
- GPU 메트릭 수집을 위한 nvidia_smi_exporter 구성 검토 (선택)

# PRD: Grafana 대시보드 드릴다운 구현

## Introduction

현재 프로젝트의 Grafana 대시보드는 각 메트릭을 독립적으로 시각화하지만, 문제 해결을 위해 대시보드 간 수동으로 이동하며 컨텍스트(시간대, 엔드포인트, 모델)를 다시 설정해야 한다. 드릴다운 기능을 추가하여 고수준 개요에서 세부 정보로 자연스럽게 내려가며 문제를 빠르게 진단할 수 있는 인터랙티브한 모니터링 경험을 제공한다.

## Goals

- 기존 4개 대시보드 간 드릴다운 링크 구현
- 엔드포인트/모델별 상세 분석을 위한 신규 대시보드 2개 추가
- 클릭 한 번으로 컨텍스트(시간대, 필터)를 유지하며 상세 정보로 이동
- 문제 발생 시 메트릭 → 상세 분석 → 로그로 연결되는 워크플로우 구축
- 모니터링 문서 업데이트 (워크플로우 시나리오 포함)

## User Stories

### US-001: inference-metrics 대시보드에 드릴다운 링크 추가

**Description:** As a 엔지니어, I want inference-metrics.json의 각 패널에서 상세 대시보드로 이동할 수 있도록 so that 성능 이슈를 빠르게 분석할 수 있다.

**Acceptance Criteria:**
- [ ] "HTTP Request Latency" 패널에 "엔드포인트 상세 보기" 링크 추가
- [ ] "LLM Request Duration" 패널에 "모델 상세 보기" 링크 추가
- [ ] 링크 클릭 시 `endpoint` 또는 `model` 변수와 시간 범위(`from`, `to`)가 자동 전달
- [ ] 모든 time-series 패널에 "관련 로그 보기" 링크 추가
- [ ] 링크가 `fieldConfig.defaults.links` 배열로 정의되어 있음
- [ ] Grafana UI에서 패널 클릭 시 드릴다운 메뉴 표시 확인

### US-002: 엔드포인트별 상세 분석 대시보드 생성

**Description:** As a 엔지니어, I want 특정 엔드포인트의 성능을 심층 분석하는 대시보드 so that 병목을 정확히 파악할 수 있다.

**Acceptance Criteria:**
- [ ] `inference-detail.json` 파일 생성 (uid: `inference-detail`)
- [ ] `$endpoint` 변수 정의 (query: `label_values(http_requests_total, endpoint)`)
- [ ] `$model` 변수 정의 (query: `label_values(llm_requests_total, model)`)
- [ ] 패널 포함: 시간대별 요청 수, p50/p95/p99 레이턴시, 에러율 시계열
- [ ] 패널 포함: 요청 크기 분포 (히스토그램), 토큰 수 분포
- [ ] 패널 포함: 모델별 성능 비교 (bar gauge)
- [ ] 패널 포함: 최근 에러 로그 (Loki 쿼리, 상위 10개)
- [ ] 모든 쿼리가 `endpoint="$endpoint"` 필터 사용
- [ ] 로그 패널에 "전체 로그 보기" 링크 추가 (logs-dashboard로 드릴다운)

### US-003: 학습 실험별 상세 분석 대시보드 생성

**Description:** As a ML 엔지니어, I want 특정 학습 실험의 메트릭을 상세히 분석하는 대시보드 so that 하이퍼파라미터 튜닝 결과를 평가할 수 있다.

**Acceptance Criteria:**
- [ ] `training-detail.json` 파일 생성 (uid: `training-detail`)
- [ ] `$experiment_id` 변수 정의 (query: `label_values(mlflow_run_status, experiment_id)`)
- [ ] `$run_id` 변수 정의 (query: `label_values(mlflow_run_status, run_id)`)
- [ ] 패널 포함: Loss curve (train/val), Learning rate 스케줄
- [ ] 패널 포함: GPU 사용률 시계열, 메모리 사용량
- [ ] 패널 포함: 체크포인트 저장 시점 (annotation)
- [ ] 패널 포함: 하이퍼파라미터 테이블 (MLflow metrics)
- [ ] 모든 쿼리가 `run_id="$run_id"` 필터 사용

### US-004: logs-dashboard에 컨텍스트 변수 추가

**Description:** As a 엔지니어, I want 로그 대시보드가 드릴다운으로 전달된 필터를 자동 적용하도록 so that 관련 로그만 즉시 확인할 수 있다.

**Acceptance Criteria:**
- [ ] `logs-dashboard.json`에 `$endpoint` 변수 추가 (type: textbox)
- [ ] `$model` 변수 추가 (type: textbox)
- [ ] `$status_code` 변수 추가 (type: custom, query: "200,400,401,403,404,500,502,503")
- [ ] Loki 쿼리를 `{job="fastapi"} | json | endpoint="$endpoint" | model="$model"` 형식으로 수정
- [ ] 변수가 비어있을 때는 필터 미적용 (정규식: `|~ ".*"` 사용)
- [ ] 시간 범위가 URL 파라미터로 전달된 경우 자동 적용

### US-005: system-overview 대시보드에 서비스별 드릴다운 추가

**Description:** As a 엔지니어, I want 전체 시스템 개요에서 특정 서비스로 드릴다운하여 so that 문제 서비스를 빠르게 격리할 수 있다.

**Acceptance Criteria:**
- [ ] "CPU Usage by Service" 패널에 서비스별 드릴다운 링크 추가
- [ ] FastAPI 서비스 클릭 시 `inference-metrics.json`로 이동
- [ ] vLLM 서비스 클릭 시 `inference-detail.json`로 이동 (model 변수 없이)
- [ ] MLflow 서비스 클릭 시 `training-metrics.json`로 이동
- [ ] 시간 범위 자동 전달

### US-006: training-metrics 대시보드에 실험 드릴다운 추가

**Description:** As a ML 엔지니어, I want 학습 개요 대시보드에서 특정 실험으로 드릴다운하여 so that 실험 결과를 상세히 분석할 수 있다.

**Acceptance Criteria:**
- [ ] "Loss by Experiment" 패널에 실험별 드릴다운 링크 추가
- [ ] 링크 클릭 시 `training-detail.json`로 이동하며 `experiment_id`, `run_id` 전달
- [ ] "GPU Utilization" 패널에도 동일한 링크 추가
- [ ] 패널 제목에 "클릭하여 상세 보기" 설명 추가

### US-007: 드릴다운 워크플로우 문서화

**Description:** As a 팀원, I want 드릴다운 사용 방법과 문제 해결 시나리오를 문서로 제공받아 so that 효과적으로 모니터링 도구를 활용할 수 있다.

**Acceptance Criteria:**
- [ ] `docs/references/GRAFANA_DRILLDOWN.md` 파일 생성
- [ ] 드릴다운 개념 설명 (다이어그램 포함)
- [ ] 문제 해결 워크플로우 시나리오 3개 이상 작성
- [ ] 각 대시보드의 드릴다운 경로 맵 제공
- [ ] 변수 사용법 및 URL 파라미터 가이드 포함
- [ ] `deployment/CLAUDE.md`에 드릴다운 섹션 추가 (참조 링크)

## Functional Requirements

- FR-1: 모든 드릴다운 링크는 `fieldConfig.defaults.links` 또는 `options.dataLinks` 사용
- FR-2: URL 형식: `/d/{dashboard-uid}?var-{variable}=${__field.labels.{label}}&from=${__from}&to=${__to}`
- FR-3: 변수 타입: `query` (Prometheus), `textbox` (URL 전달용), `custom` (고정값)
- FR-4: 링크 제목은 한글로 작성 (예: "엔드포인트 상세 보기")
- FR-5: 모든 신규 대시보드는 기존 naming convention 따름 (이모지 + 영어 제목)
- FR-6: Loki 쿼리는 변수 필터가 optional하게 동작 (빈 값 허용)
- FR-7: 대시보드 JSON은 `schemaVersion: 38` 유지

## Non-Goals

- 대시보드 UI/UX 전면 재설계
- 새로운 메트릭 수집 (기존 Prometheus/Loki 데이터만 사용)
- 알람/알럿 규칙 추가
- 외부 대시보드 공유 기능
- 모바일 반응형 최적화

## Technical Considerations

- Grafana 변수 문법: `$variable` (패널 쿼리), `${__field.labels.name}` (링크 템플릿)
- URL 전달 변수: `from`, `to` (Unix timestamp ms), `var-{name}={value}`
- Loki LogQL 조건부 필터: `| endpoint=~"${endpoint:-.+}"` (빈 값 시 모든 값 매칭)
- 기존 대시보드 파일 크기: inference-metrics.json (500줄) → +100줄 예상
- 신규 대시보드 예상 크기: 각 600-800줄
- Prometheus 레이블 확인 필요: `endpoint`, `model`, `status_code` 레이블 존재 여부 검증

## Success Metrics

- 전체 대시보드 수: 4개 → 6개
- 드릴다운 링크 수: 20개 이상
- 각 대시보드에서 1-2번의 클릭으로 로그까지 도달 가능
- 문제 해결 시간 단축: 수동 네비게이션 5-10분 → 드릴다운 1-2분
- 모든 링크의 변수/시간 범위 전달 성공률 100%

## Open Questions

- Prometheus에 `endpoint`, `model` 레이블이 모든 관련 메트릭에 일관되게 붙어있는가?
- Loki 로그에 `endpoint`, `model` 필드가 JSON 파싱 후 사용 가능한가?
- MLflow 메트릭이 Prometheus로 수집되고 있는가? (training-detail 대시보드용)
- 대시보드 provisioning 설정이 신규 JSON 파일을 자동으로 로드하는가?

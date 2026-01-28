# PRD: Alloy-Loki 로그 수집 문제 해결

## Introduction/Overview

통합 테스트(feature/logging-integration-test) 중 Alloy가 로그 파일을 읽고 있으나 Loki에 실제 데이터가 저장되지 않는 문제가 발견되었다. Grafana에서 로그를 조회할 수 없어 모니터링 시스템이 제대로 작동하지 않는다. JSON 로그 처리 파이프라인 또는 Loki 수집 설정을 수정하여 로그가 정상적으로 저장되도록 해야 한다.

## Goals

1. Alloy가 수집한 로그가 Loki에 정상적으로 저장되도록 수정
2. Grafana에서 모든 서비스(FastAPI, vLLM, MLflow) 로그 조회 가능하도록 검증
3. 파일 기반 로그 수집 또는 Docker stdout 로그 수집 중 적합한 방식 선택 및 구현
4. 로그 수집 파이프라인의 각 단계(수집 → 처리 → 저장 → 조회)가 정상 작동하는지 확인

## User Stories

### US-001: Alloy JSON 처리 파이프라인 디버깅

**As a** DevOps 엔지니어
**I want** Alloy의 JSON 로그 처리 파이프라인이 올바르게 작동하는지 확인하고 싶다
**So that** FastAPI의 JSON 로그가 Loki에 정상 저장될 수 있다

**Acceptance Criteria:**
- deployment/monitoring/configs/alloy/config.alloy의 loki.process.json_logs 설정 검토
- FastAPI 로그 형식과 Alloy JSON 파싱 설정 일치 여부 확인
- 간단한 테스트 로그로 JSON 파싱 동작 검증
- Alloy 로그에서 JSON 파싱 에러 또는 경고 확인
- 문제 발견 시 JSON expressions 또는 stage 설정 수정
- Typecheck passes

### US-002: Loki 수집 확인 및 간단한 테스트

**As a** 개발자
**I want** 최소한의 설정으로 Loki 로그 수집이 작동하는지 확인하고 싶다
**So that** 문제가 Alloy 설정인지 Loki 자체인지 파악할 수 있다

**Acceptance Criteria:**
- Alloy에서 간단한 텍스트 로그 소스 추가 (JSON 파싱 없이)
- 텍스트 로그가 Loki에 정상 저장되는지 확인
- Loki API로 쿼리하여 데이터 조회 성공 확인
- JSON 처리가 문제인지, Loki 연결이 문제인지 판단
- 문제 원인에 따라 다음 단계 결정
- Typecheck passes

### US-003: Docker stdout 로그 수집 검증

**As a** DevOps 엔지니어
**I want** 파일 기반 로그 수집 대신 Docker stdout 로그 수집이 작동하는지 확인하고 싶다
**So that** 더 간단하고 안정적인 로그 수집 방식을 사용할 수 있다

**Acceptance Criteria:**
- Alloy의 loki.source.docker 설정이 올바르게 동작하는지 확인
- FastAPI 컨테이너의 stdout 로그가 Loki에 수집되는지 검증
- Grafana에서 {service="fastapi"} 쿼리로 Docker 로그 조회
- 파일 기반 로그와 Docker 로그 중 어느 것을 사용할지 결정
- 선택한 방식으로 모든 서비스 로그 수집 설정
- Typecheck passes

### US-004: 모든 서비스 로그 Grafana 조회 테스트

**As a** 개발자
**I want** Grafana에서 모든 서비스의 로그를 조회할 수 있는지 확인하고 싶다
**So that** 실시간 로그 모니터링이 가능한지 검증할 수 있다

**Acceptance Criteria:**
- Grafana UI(http://localhost:3000)에서 Explore 메뉴 접근
- {job="fastapi"} 쿼리로 FastAPI 로그 조회 성공
- {job="vllm"} 쿼리로 vLLM 로그 조회 성공 (로그 파일 생성 시)
- {job="mlflow"} 쿼리로 MLflow 로그 조회 성공
- 각 서비스별로 최소 1개 이상의 로그 엔트리 확인
- 로그 내용이 올바르게 표시되는지 확인 (타임스탬프, 메시지, 레벨 등)
- Typecheck passes

### US-005: 로그 수집 문제 해결 방법 문서화

**As a** 개발자
**I want** 로그 수집 문제 해결 과정과 최종 설정을 문서화하고 싶다
**So that** 향후 유사한 문제 발생 시 빠르게 해결할 수 있다

**Acceptance Criteria:**
- deployment/CLAUDE.md에 로그 수집 트러블슈팅 섹션 추가
- 발견한 문제와 해결 방법 기록 (JSON 파싱, Loki 설정 등)
- Alloy 설정 검증 방법 문서화 (로그 확인, API 테스트 등)
- Grafana 로그 쿼리 예시 추가
- 최종 작동하는 Alloy 설정 설명 추가
- Typecheck passes

## Functional Requirements

**FR-1**: Alloy는 모든 서비스 로그를 Loki에 정상적으로 전송해야 한다
**FR-2**: Loki는 수신한 로그를 저장하고 쿼리 가능하게 해야 한다
**FR-3**: Grafana에서 Loki 데이터소스를 통해 로그를 조회할 수 있어야 한다
**FR-4**: JSON 로그는 구조화되어 저장되고 필드별 필터링이 가능해야 한다
**FR-5**: 로그 수집 실패 시 Alloy 로그에 명확한 에러 메시지가 표시되어야 한다

## Non-Goals

- Grafana 대시보드 생성
- 로그 보관 기간 설정
- 로그 알림 설정
- 성능 최적화

## Technical Considerations

- Alloy v1.4.2의 loki.source.file과 loki.process 기능 사용
- FastAPI 로그는 structlog으로 JSON 형식 출력
- Loki v2.9.0의 기본 설정 사용
- 현재 Alloy 로그에 JSON 파싱 에러가 없음 (숨겨진 문제일 가능성)
- Docker stdout 로그는 이미 수집 설정되어 있으나 파일 로그와 중복될 수 있음

## Success Metrics

- [ ] Alloy가 로그를 Loki로 성공적으로 전송
- [ ] Loki API 쿼리로 로그 데이터 조회 가능
- [ ] Grafana Explore에서 모든 서비스 로그 조회 성공
- [ ] JSON 로그 필드가 올바르게 파싱되고 라벨로 추출됨
- [ ] 로그 수집 파이프라인 문서화 완료

## Open Questions

- JSON 파싱 실패가 조용히(silent) 일어나고 있는가?
- Loki의 ingestion 설정에 문제가 있는가?
- 파일 기반 로그 대신 Docker stdout 로그만 사용해야 하는가?
- Alloy의 loki.write 설정에 추가 옵션이 필요한가?

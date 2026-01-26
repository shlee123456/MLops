# PRD: GPU Device Allocation for vLLM Server

## Introduction/Overview

현재 MLOps 프로젝트의 Docker Compose 설정에서 vLLM 서버는 `count: 1` 설정으로 랜덤하게 1개의 GPU를 할당받습니다. 이로 인해 사용자가 특정 GPU를 지정할 수 없으며, GPU 0 (RTX 5090, 32GB)과 GPU 1 (RTX 5060 Ti, 16GB) 중 어느 것이 사용될지 예측할 수 없습니다.

이 기능은 환경변수를 통해 특정 GPU 번호를 지정할 수 있도록 하여, 사용자가 프로덕션 서빙과 학습/테스트를 별도의 GPU에서 수행할 수 있게 합니다.

## Goals

1. Docker Compose에서 환경변수(`GPU_DEVICE_ID`)로 특정 GPU 번호를 지정할 수 있도록 한다
2. 기존 기능에 영향을 주지 않으며, 기본값(GPU 0)으로 동작하도록 한다
3. `.env` 파일과 명령줄 모두에서 GPU 번호를 설정할 수 있도록 한다
4. GPU 할당 상태를 확인할 수 있는 방법을 제공한다

## User Stories

### US-001: Docker Compose GPU 설정 변경

**As a** DevOps 엔지니어
**I want** Docker Compose에서 특정 GPU를 지정할 수 있도록
**So that** 프로덕션 서빙과 학습을 별도 GPU에서 수행할 수 있다

**Acceptance Criteria:**
- `docker/docker-compose.serving.yml`에서 `count: 1` 제거
- `device_ids: ['${GPU_DEVICE_ID:-0}']` 추가
- 환경변수가 없으면 GPU 0을 기본값으로 사용
- 기존 vLLM 서버 기능에 영향 없음
- Typecheck passes

**Priority:** 1

---

### US-002: 환경변수 파일 업데이트

**As a** 개발자
**I want** `.env`와 `env.example`에 GPU_DEVICE_ID 설정이 문서화되어 있도록
**So that** GPU 번호를 쉽게 설정하고 이해할 수 있다

**Acceptance Criteria:**
- `.env` 파일에 `GPU_DEVICE_ID=0` 추가
- `env.example`에 GPU_DEVICE_ID 설명 추가 (GPU 0: RTX 5090, GPU 1: RTX 5060 Ti)
- 주석으로 GPU별 스펙 정보 포함
- Typecheck passes

**Priority:** 2

---

### US-003: GPU 할당 검증 스크립트 생성

**As a** 시스템 관리자
**I want** GPU 할당 상태를 확인하는 스크립트가 있도록
**So that** vLLM 서버가 의도한 GPU에서 실행되고 있는지 검증할 수 있다

**Acceptance Criteria:**
- `scripts/check_gpu_allocation.sh` 스크립트 생성
- 시스템 GPU 상태 출력 (nvidia-smi)
- 컨테이너 GPU 할당 정보 출력 (docker inspect)
- vLLM 프로세스 GPU 사용량 출력
- 실행 권한 부여 (chmod +x)
- Typecheck passes

**Priority:** 3

---

### US-004: 문서화 업데이트

**As a** 팀원
**I want** GPU 할당 방법이 문서에 설명되어 있도록
**So that** GPU 설정 방법을 이해하고 사용할 수 있다

**Acceptance Criteria:**
- `deployment/CLAUDE.md`에 GPU 설정 섹션 추가
- GPU 번호 지정 방법 설명
- 사용 예시 포함 (GPU 0 사용, GPU 1 사용)
- 학습과 서빙 분리 예시 포함
- Typecheck passes

**Priority:** 4

---

### US-005: 통합 테스트

**As a** QA 엔지니어
**I want** GPU 할당이 올바르게 동작하는지 검증하도록
**So that** 배포 전 기능이 정상 작동함을 확인할 수 있다

**Acceptance Criteria:**
- GPU 0 지정 후 vLLM 서버 실행 성공
- `docker inspect`로 GPU 0 할당 확인
- `nvidia-smi`로 GPU 0에서만 프로세스 실행 확인
- GPU 1로 변경 후 동일하게 확인
- API 응답 정상 (`curl http://localhost:8000/v1/models`)
- Typecheck passes

**Priority:** 5

## Functional Requirements

### FR-1: GPU Device ID 환경변수 지원
Docker Compose는 `GPU_DEVICE_ID` 환경변수를 읽어 특정 GPU를 할당해야 한다.
- 기본값: 0 (GPU 0, RTX 5090)
- 허용값: 0 또는 1
- 환경변수 미설정 시 GPU 0 사용

### FR-2: Docker Compose device_ids 설정
`deploy.resources.reservations.devices`에서 `device_ids` 배열을 사용하여 GPU를 지정해야 한다.

### FR-3: 환경변수 우선순위
1. 명령줄 환경변수 (`GPU_DEVICE_ID=1 docker compose up`)
2. `.env` 파일
3. Docker Compose 기본값 (`${GPU_DEVICE_ID:-0}`)

### FR-4: 검증 도구 제공
GPU 할당 상태를 확인할 수 있는 셸 스크립트를 제공해야 한다.

## Non-Goals

다음은 이번 작업 범위에 포함되지 않는다:

1. **여러 모델 동시 서빙**: 다중 vLLM 서버 인스턴스 실행 (별도 PRD 필요)
2. **Tensor Parallel 지원**: 단일 모델을 여러 GPU에서 병렬 처리 (별도 PRD 필요)
3. **동적 GPU 스케줄링**: 런타임에 GPU 변경
4. **GPU 메모리 모니터링**: Prometheus/Grafana 연동 (기존 모니터링 스택 활용)
5. **자동 GPU 선택**: GPU 사용률 기반 자동 할당

## Technical Considerations

### 1. Docker Compose GPU 할당 방식

Docker Compose는 두 가지 GPU 할당 방식을 지원한다:
- `count: N` - 사용 가능한 GPU 중 N개를 랜덤 할당
- `device_ids: [...]` - 특정 GPU ID 지정

이번 작업에서는 `device_ids`를 사용하여 특정 GPU를 지정한다.

### 2. GPU 스펙 차이

| GPU | VRAM | 추정 성능 | 권장 용도 |
|-----|------|----------|----------|
| GPU 0: RTX 5090 | 32GB | ~100 tokens/s | 프로덕션 서빙 |
| GPU 1: RTX 5060 Ti | 16GB | ~60 tokens/s | 테스트/개발 |

### 3. 기존 코드와의 호환성

- 기존 학습 스크립트는 `CUDA_VISIBLE_DEVICES` 환경변수 사용
- vLLM 서버는 Docker Compose의 GPU 할당만 따름
- 두 방식은 독립적으로 동작하므로 충돌 없음

### 4. 롤백 전략

변경사항이 적어 롤백이 간단함:
```bash
git checkout docker/docker-compose.serving.yml
docker compose -f docker/docker-compose.serving.yml restart
```

## Success Metrics

1. **기능 완료도**: 모든 User Story의 Acceptance Criteria 통과
2. **GPU 할당 정확도**: 지정한 GPU에서 vLLM 서버 실행 (100%)
3. **API 응답 성공률**: GPU 변경 후에도 API 정상 동작 (100%)
4. **문서 완성도**: GPU 설정 방법이 명확히 문서화됨
5. **작업 시간**: 20-25분 이내 완료

## Open Questions

1. **GPU 2개 이상 환경**: 현재는 GPU 0, 1만 지원. 3개 이상일 때 확장 방법은?
   - 답변: 현재는 2개 GPU만 있으므로 하드코딩. 필요 시 추후 확장

2. **GPU 할당 실패 처리**: 존재하지 않는 GPU ID를 지정하면?
   - 답변: Docker가 에러를 발생시킴. 문서에 명시

3. **Runtime GPU 변경**: 서버 실행 중 GPU 변경 필요 시?
   - 답변: 컨테이너 재시작 필요. 다운타임 발생

## Dependencies

- Docker Compose 1.28+ (GPU 지원)
- NVIDIA Docker Runtime
- nvidia-container-toolkit

## Timeline

- US-001: 5분
- US-002: 5분
- US-003: 10분
- US-004: 5분
- US-005: 10-15분
- **총 예상 시간**: 35-40분

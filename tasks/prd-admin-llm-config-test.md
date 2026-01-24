# PRD: Admin LLM Config 설정 기능 테스트

## Introduction

Admin 페이지(`LLMConfigAdmin`)와 API 엔드포인트(`/v1/llm-configs`)를 통한 LLM 설정 CRUD 기능의 통합 테스트를 작성한다. 기존 테스트가 HTTP 상태 코드만 확인하는 수준인 반면, 이 PRD는 실제 DB 데이터 영속화, 유효성 검증, `is_default` 중복 방지 로직 등 실제 동작을 검증하는 테스트를 목표로 한다.

## Goals

- LLMConfig의 전체 CRUD 흐름을 실제 DB 기반으로 검증
- 모든 필드(name, model_name, system_prompt, temperature, max_tokens, top_p, is_default)의 정상 저장/반환 확인
- `is_default` 플래그의 중복 방지(기존 기본값 자동 해제) 로직 검증
- 유효성 검증 실패 시 적절한 에러 응답 확인
- Admin UI CRUD와 API 엔드포인트 양쪽 모두 테스트
- 누락된 API 엔드포인트(수정/삭제) 추가 및 테스트

## User Stories

### US-001: LLM Config API 생성 테스트
**Description:** As a 개발자, I want LLM Config 생성 API가 모든 필드를 정확히 저장하는지 검증 so that 데이터 무결성을 보장할 수 있다.

**Acceptance Criteria:**
- [ ] `POST /v1/llm-configs`로 모든 필드 포함한 설정 생성 시 201 응답
- [ ] 응답 body에 id, name, model_name, system_prompt, temperature, max_tokens, top_p, is_default, created_at 필드 포함
- [ ] 필수 필드(name, model_name) 누락 시 422 에러 응답
- [ ] temperature 범위 초과(0~2) 시 422 에러 응답
- [ ] max_tokens 범위 초과(1~4096) 시 422 에러 응답
- [ ] top_p 범위 초과(0~1) 시 422 에러 응답
- [ ] `python -m pytest tests/serve/ -v` 통과

### US-002: LLM Config API 조회 테스트
**Description:** As a 개발자, I want LLM Config 목록/상세 조회 API가 정확한 데이터를 반환하는지 검증 so that 클라이언트가 올바른 정보를 받을 수 있다.

**Acceptance Criteria:**
- [ ] `GET /v1/llm-configs`로 생성한 설정 목록 조회 가능
- [ ] 목록이 name 순으로 정렬되어 반환
- [ ] `GET /v1/llm-configs/{id}`로 특정 설정 조회 시 모든 필드 일치 확인
- [ ] 존재하지 않는 ID 조회 시 404 에러 응답
- [ ] `python -m pytest tests/serve/ -v` 통과

### US-003: LLM Config API 수정/삭제 엔드포인트 추가
**Description:** As a 개발자, I want LLM Config의 수정(PUT)과 삭제(DELETE) API를 추가 so that 전체 CRUD가 가능하다.

**Acceptance Criteria:**
- [ ] `PUT /v1/llm-configs/{id}` 엔드포인트 추가 (cruds, routers, schemas)
- [ ] `DELETE /v1/llm-configs/{id}` 엔드포인트 추가 (cruds, routers)
- [ ] 수정 시 부분 업데이트 가능 (변경하지 않는 필드는 유지)
- [ ] 삭제 시 해당 Config를 참조하는 Conversation의 llm_config_id가 NULL 처리
- [ ] 존재하지 않는 ID 수정/삭제 시 404 에러 응답
- [ ] `python -m pytest tests/serve/ -v` 통과

### US-004: is_default 중복 방지 로직 테스트
**Description:** As a 개발자, I want is_default=true인 Config가 항상 하나만 존재하도록 검증 so that 기본 설정 충돌을 방지할 수 있다.

**Acceptance Criteria:**
- [ ] 새 Config를 is_default=true로 생성하면 기존 default Config가 자동으로 false로 변경
- [ ] 기존 Config를 is_default=true로 수정해도 동일하게 기존 default가 해제
- [ ] is_default=true인 Config가 없는 상태에서 새로 설정 가능
- [ ] DB에서 직접 조회하여 is_default=true가 항상 0~1개임을 확인
- [ ] `python -m pytest tests/serve/ -v` 통과

### US-005: Admin UI를 통한 LLMConfig CRUD 테스트
**Description:** As a 관리자, I want Admin 페이지에서 LLM 설정을 생성/조회/수정/삭제할 수 있음을 검증 so that UI 기반 관리가 신뢰할 수 있다.

**Acceptance Criteria:**
- [ ] `/admin/llm-config/list` 페이지 접근 시 200 응답 및 설정 목록 표시
- [ ] `/admin/llm-config/create` 페이지에서 설정 생성 가능
- [ ] `/admin/llm-config/details/{id}` 페이지에서 상세 정보 확인 가능
- [ ] `/admin/llm-config/edit/{id}` 페이지에서 설정 수정 가능
- [ ] `/admin/llm-config/delete/{id}`로 설정 삭제 가능
- [ ] name, model_name 필드로 검색 기능 동작 확인
- [ ] `python -m pytest tests/serve/ -v` 통과

## Functional Requirements

- FR-1: `PUT /v1/llm-configs/{id}` 엔드포인트 - LLMConfig 수정 (Pydantic 스키마 유효성 검증 포함)
- FR-2: `DELETE /v1/llm-configs/{id}` 엔드포인트 - LLMConfig 삭제 (참조 Conversation NULL 처리)
- FR-3: `update_llm_config` CRUD 함수 - 부분 업데이트, is_default 중복 방지 포함
- FR-4: `delete_llm_config` CRUD 함수 - 삭제 및 FK 관계 정리
- FR-5: 테스트에서 실제 DB 세션을 사용하여 데이터 영속화 검증
- FR-6: 각 테스트는 독립적으로 실행 가능 (테스트 간 데이터 오염 없음)
- FR-7: Admin UI 테스트는 로그인 후 세션 유지하여 CRUD 수행

## Non-Goals

- Admin UI의 시각적/디자인 검증 (브라우저 렌더링 테스트 제외)
- vLLM 서버와의 실제 연동 테스트
- 성능/부하 테스트
- LLMConfig와 연결된 Conversation의 채팅 동작 테스트

## Technical Considerations

- 테스트 파일: `tests/serve/test_llm_config.py` (독립 파일로 분리)
- 기존 `conftest.py`의 `client`, `test_db` 픽스처 재사용
- Admin 테스트 시 `extract_csrf_token` 헬퍼는 conftest로 이동 고려
- `name` 필드에 unique 제약이 있으므로 중복 생성 테스트 포함
- SQLAdmin의 URL 패턴: `/admin/{model-name}/list`, `/admin/{model-name}/create` 등

## Success Metrics

- LLMConfig CRUD 전체 흐름을 커버하는 테스트 20개 이상
- 유효성 검증 실패 케이스 포함 (경계값 테스트)
- `is_default` 로직의 엣지 케이스 검증
- `python -m pytest tests/serve/ -v` 전체 통과

## Open Questions

- Admin UI의 model URL 패턴이 `llm-config`인지 `llmconfig`인지 확인 필요 (SQLAdmin 자동 생성 규칙)
- unique 제약 위반 시 SQLAdmin이 어떤 에러를 반환하는지 확인 필요

# PRD: Admin UI 필드 개선

## Overview

현재 Admin 페이지에서 User 생성 시 비밀번호 필드가 없어 NULL 제약 조건 에러가 발생하고, Role 및 LLM Model 필드에서 드롭다운/자동완성이 없어 사용성이 떨어지는 문제를 해결합니다.

## Goals

1. **User 생성 시 비밀번호 필드 에러 해결** - Admin에서 User 생성 시 비밀번호를 입력받아 자동 해싱
2. **Role 선택 UX 개선** - 텍스트 입력 대신 드롭다운으로 변경하여 오타 방지
3. **LLM Model 입력 가이드 제공** - API URL 및 토큰 제한 필드에 예시와 기본값 제공

## User Stories

### US-001: User Admin 비밀번호 필드 추가 (버그 픽스)
**As a** 관리자
**I want** Admin UI에서 User 생성 시 비밀번호를 입력하고 싶다
**So that** 비밀번호가 자동으로 해싱되어 저장되고 NULL 에러가 발생하지 않는다

**Acceptance Criteria:**
- `UserAdmin.form_extra_fields`에 `password` PasswordField 추가
- `insert_model`에서 비밀번호 해싱 처리 (bcrypt)
- 신규 생성 시 비밀번호 없으면 에러 메시지 표시
- `update_model`에서 비밀번호 입력 시에만 변경, 비워두면 기존 비밀번호 유지
- bcrypt<4.2.0 버전 제약 조건 확인 (requirements.txt)
- 테스트 추가: User 생성/수정 시나리오
- Typecheck passes

### US-002: User Admin Role 드롭다운
**As a** 관리자
**I want** User 생성/수정 시 role을 드롭다운에서 선택하고 싶다
**So that** 오타로 인한 잘못된 role 입력을 방지할 수 있다

**Acceptance Criteria:**
- `UserAdmin.form_overrides`에 role을 SelectField로 오버라이드
- 선택지: UserRole enum 값 기반 (admin, user, guest)
- 기본값: user
- 폼에서 드롭다운으로 표시 확인
- Typecheck passes

### US-003: LLM Model Admin 필드 가이드 추가
**As a** 관리자
**I want** LLM Model 생성 시 API URL과 max_tokens_limit에 예시가 표시되면 좋겠다
**So that** 올바른 형식으로 쉽게 입력할 수 있다

**Acceptance Criteria:**
- `LLMModelAdmin.form_args`에 api_url placeholder 추가 (예: "http://localhost:8000/v1")
- api_url description 추가: "vLLM OpenAI 호환 엔드포인트 URL"
- max_tokens_limit 기본값 설정 (2048)
- max_tokens_limit description 추가: "이 모델이 생성할 수 있는 최대 토큰 수"
- 폼에서 placeholder 및 description 표시 확인
- Typecheck passes

## Functional Requirements

### FR-1: User 비밀번호 처리
- 생성 시: 비밀번호 필수, bcrypt로 해싱하여 password_hash 저장
- 수정 시: 비밀번호 입력하면 새 해시로 변경, 비워두면 기존 유지
- 비밀번호 필드는 PasswordField 타입 (마스킹 표시)

### FR-2: Role 선택 제한
- UserAdmin의 role 필드는 SelectField로 표시
- 선택 가능한 값: admin, user, guest (UserRole enum)
- DB 저장 시 enum value로 저장

### FR-3: LLM Model 입력 가이드
- api_url 필드에 placeholder와 description 제공
- max_tokens_limit에 기본값 2048 설정
- form_args를 통한 필드별 커스터마이징

## Non-Goals

- 비밀번호 복잡도 검증 (향후 추가 가능)
- 비밀번호 변경 이력 추적
- User bulk 생성 기능
- LLM Model API URL 유효성 검증 (향후 추가 가능)

## Technical Considerations

### 의존성
- `wtforms` - SelectField 사용
- `bcrypt<4.2.0` - passlib 1.7.4 호환성 (이미 적용됨)

### 파일 수정
- `src/serve/admin/views.py` - UserAdmin, LLMModelAdmin 수정
- `tests/serve/test_user_admin.py` - 신규 테스트 파일 생성

### 기존 코드 영향
- UserAdmin: `insert_model`, `update_model` 메서드 오버라이드 (이미 적용됨)
- 기존 테스트는 영향 없음 (추가 테스트만 작성)

## Success Metrics

- ✅ Admin에서 User 생성 시 비밀번호 입력 필드 표시
- ✅ 비밀번호 없이 User 생성 시도 시 에러 메시지 표시
- ✅ Role 드롭다운에서 3개 선택지 확인
- ✅ LLM Model 생성 시 api_url placeholder 표시
- ✅ 모든 테스트 통과 (기존 60개 + 신규 4개)

## Open Questions

- ❓ 비밀번호 최소 길이 제한이 필요한가? (향후 고려)
- ❓ LLM Model의 api_key 마스킹은 목록에서만 숨기는 것이 충분한가? (현재 구현 유지)

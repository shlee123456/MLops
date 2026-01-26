# PRD: Admin UI 비밀번호 필드 렌더링 버그 수정

## 개요

SQLAdmin의 UserAdmin 뷰에서 `form_extra_fields`로 추가한 비밀번호 필드가 실제 브라우저 UI에 렌더링되지 않는 버그를 수정한다.

## 문제 상황

**현재 상태**:
- `src/serve/admin/views.py`의 `UserAdmin`에 `form_extra_fields`로 password 필드 정의됨
- `form_create_rules`, `form_edit_rules`로 필드 순서 명시
- pytest 테스트는 모두 통과 (API 레벨에서는 정상 작동)
- **하지만 브라우저에서 http://localhost:8080/admin/user/create 접속 시 password 필드가 보이지 않음**

**현재 보이는 필드**:
- Username
- 역할 (Role)
- Is Active
- ~~비밀번호~~ ← 보이지 않음

**환경**:
- SQLAdmin 0.22.0
- Docker Compose로 실행 중
- 볼륨 마운트: `../src:/app/src`

## 목표

1. **필드 렌더링**: Admin UI에서 비밀번호 필드를 실제로 표시
2. **기능 검증**: 브라우저에서 User 생성/수정 시 비밀번호 입력 가능
3. **테스트 유지**: 기존 테스트 통과 유지

## 사용자 스토리

### US-001: SQLAdmin form_extra_fields 렌더링 조사
**As a** 개발자
**I want** form_extra_fields가 왜 렌더링되지 않는지 원인을 파악하고 싶다
**So that** 올바른 해결 방법을 적용할 수 있다

**인수 조건**:
- [ ] SQLAdmin 0.22.0 문서에서 form_extra_fields 사용법 확인
- [ ] SQLAdmin GitHub Issues/Discussions에서 유사 사례 검색
- [ ] 로컬에서 최소 재현 코드 작성하여 테스트
- [ ] 원인을 progress.txt에 기록 (템플릿 문제 / 설정 문제 / 버그 등)

### US-002: 커스텀 템플릿 방식으로 해결 시도
**As a** 개발자
**I want** SQLAdmin 커스텀 템플릿을 사용하여 password 필드를 명시적으로 렌더링하고 싶다
**So that** form_extra_fields의 한계를 우회할 수 있다

**인수 조건**:
- [ ] `src/serve/admin/templates/user_create.html` 생성
- [ ] Jinja2 템플릿에서 password 필드 명시적으로 추가
- [ ] UserAdmin에 `create_template = "user_create.html"` 설정
- [ ] 브라우저에서 Create 페이지 접속 시 password 필드 확인
- [ ] Typecheck passes

**의존성**: US-001 (원인 파악 후 시도)

### US-003: form_include_columns 방식으로 해결 시도
**As a** 개발자
**I want** form_excluded_columns 대신 form_include_columns를 사용해보고 싶다
**So that** 필드 포함 방식으로 명시적으로 제어할 수 있다

**인수 조건**:
- [ ] form_excluded_columns 제거
- [ ] 사용 가능한 모든 필드 나열 후 password 포함 여부 확인
- [ ] SQLAdmin 내부 코드 분석하여 extra_fields 처리 방식 확인
- [ ] 브라우저에서 확인
- [ ] Typecheck passes

**의존성**: US-001

### US-004: scaffold_form 오버라이드 방식
**As a** 개발자
**I want** UserAdmin.scaffold_form()을 직접 오버라이드하고 싶다
**So that** 폼 생성 로직을 완전히 제어할 수 있다

**인수 조건**:
- [ ] `async def scaffold_form(self)` 메서드 오버라이드
- [ ] 기본 폼에 password 필드를 수동으로 추가
- [ ] 브라우저에서 확인
- [ ] tests/serve/test_user_admin.py 모두 통과
- [ ] Typecheck passes

**의존성**: US-002, US-003 (두 방법이 실패한 경우)

### US-005: WTForms 직접 통합 (최후의 수단)
**As a** 개발자
**I want** SQLAdmin의 자동 폼 생성을 우회하고 WTForms를 직접 사용하고 싶다
**So that** 완전한 제어권을 가질 수 있다

**인수 조건**:
- [ ] UserAdmin에 `form` 속성 직접 정의 (WTForms Form 클래스)
- [ ] username, password, role, is_active 필드 모두 수동 정의
- [ ] insert_model, update_model 로직 유지
- [ ] 브라우저에서 확인
- [ ] tests/serve/test_user_admin.py 모두 통과
- [ ] Typecheck passes

**의존성**: US-004 (이전 방법들이 모두 실패한 경우)

### US-006: 해결 방법 문서화 및 테스트 강화
**As a** 개발자
**I want** 최종 해결 방법을 문서화하고 브라우저 테스트를 추가하고 싶다
**So that** 향후 유사한 문제를 방지할 수 있다

**인수 조건**:
- [ ] `src/serve/admin/CLAUDE.md`에 해결 방법 및 주의사항 추가
- [ ] progress.txt에 최종 해결 방법 및 학습 내용 기록
- [ ] 선택사항: Playwright 기반 E2E 테스트 추가 (브라우저 자동화)
- [ ] README 또는 문서에 Admin UI 사용법 업데이트

**의존성**: US-002~US-005 중 하나 성공 후

## 성공 지표

- [ ] http://localhost:8080/admin/user/create 페이지에서 "비밀번호" 필드 확인
- [ ] 브라우저에서 User 생성 시 비밀번호 입력 및 저장 성공
- [ ] 기존 pytest 테스트 모두 통과
- [ ] Docker 컨테이너에서 정상 작동

## 기술 제약

- SQLAdmin 0.22.0 버전 고정 (업그레이드 금지)
- 기존 API 하위 호환성 유지
- Docker Compose 환경에서 작동 필수

## 우선순위

1. **US-001**: 원인 파악 (필수)
2. **US-002**: 커스텀 템플릿 (가장 간단한 해결책)
3. **US-003**: form_include_columns (설정 기반)
4. **US-004**: scaffold_form 오버라이드 (중간 복잡도)
5. **US-005**: WTForms 직접 통합 (최후의 수단)
6. **US-006**: 문서화 (해결 후)

## 비고

- 테스트는 통과하지만 UI가 작동하지 않는 경우 → 템플릿 렌더링 문제 가능성 높음
- SQLAdmin은 Jinja2 템플릿 기반 → 커스텀 템플릿으로 해결 가능
- 브라우저 개발자 도구에서 HTML 소스 확인 필요

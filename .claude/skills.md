# Skills

## /commit

Git 커밋을 수행합니다.

### 규칙
- 커밋 메시지는 한글로 작성
- Co-Authored-By 헤더 제외
- 커밋 메시지 형식: `{변경 유형}: {변경 내용 요약}`

### 변경 유형 예시
- `추가`: 새로운 기능/파일 추가
- `수정`: 기존 기능 수정
- `삭제`: 기능/파일 삭제
- `리팩토링`: 코드 구조 개선
- `문서`: 문서 추가/수정
- `버그수정`: 버그 수정
- `설정`: 설정 파일 변경

### 실행 절차
1. `git status`로 변경사항 확인
2. `git diff`로 변경 내용 확인
3. `git log --oneline -3`으로 최근 커밋 스타일 확인
4. 변경사항 분석 후 적절한 커밋 메시지 작성
5. `git add` 및 `git commit` 실행
6. 필요시 `git push` 실행

### 커밋 메시지 예시
```
추가: 사용자 인증 기능 구현
수정: 로그인 페이지 UI 개선
버그수정: 세션 만료 시 리다이렉트 오류 해결
문서: API 가이드 문서 추가
```

## /prd

기능에 대한 PRD(Product Requirements Document)를 생성합니다.

### 트리거
- "PRD 작성해줘", "기능 기획", "요구사항 정리"

### 실행 절차

1. 사용자로부터 기능 설명을 받는다
2. 3-5개의 핵심 질문을 묻는다 (선택지 포함, A/B/C/D 형식)
   - 문제/목표: 어떤 문제를 해결하는가?
   - 핵심 기능: 주요 동작은?
   - 범위/경계: 하지 않을 것은?
   - 성공 기준: 완료 조건은?
3. 답변을 바탕으로 구조화된 PRD를 생성한다
4. `tasks/prd-[기능명].md`에 저장한다

**중요:** 구현은 하지 않는다. PRD만 작성한다.

### PRD 구조

1. **Introduction/Overview** - 기능 설명과 해결할 문제
2. **Goals** - 구체적이고 측정 가능한 목표
3. **User Stories** - 각 스토리에 ID(US-001), 설명, 수용 기준 포함
4. **Functional Requirements** - FR-1, FR-2 형식의 기능 요구사항
5. **Non-Goals** - 범위 밖 항목
6. **Design Considerations** - UI/UX 요구사항 (선택)
7. **Technical Considerations** - 기술 제약사항 (선택)
8. **Success Metrics** - 성공 측정 방법
9. **Open Questions** - 미결 질문

### 스토리 규칙
- 각 스토리는 한 번의 컨텍스트 윈도우에서 완료 가능한 크기
- 수용 기준은 검증 가능해야 함 ("올바르게 동작" ❌ → "삭제 전 확인 다이얼로그 표시" ✅)
- 모든 스토리에 "Typecheck passes" 포함
- UI 스토리에는 "브라우저에서 확인" 포함
- 형식: `tasks/prd-[feature-name].md` (kebab-case)

## /ralph

PRD 마크다운을 Ralph 자율 에이전트용 `prd.json`으로 변환합니다.

### 트리거
- "PRD를 JSON으로 변환", "ralph 형식으로", "prd.json 생성"

### 실행 절차

1. 지정된 PRD 파일 (`tasks/prd-*.md`) 읽기
2. 기존 `scripts/ralph/prd.json`이 있으면 브랜치명 비교
3. 브랜치명이 다르고 progress.txt에 내용이 있으면 아카이브
4. PRD의 User Stories를 JSON 형식으로 변환
5. `scripts/ralph/prd.json`에 저장

### 출력 형식

```json
{
  "project": "[프로젝트명]",
  "branchName": "ralph/[feature-name-kebab-case]",
  "description": "[기능 설명]",
  "userStories": [
    {
      "id": "US-001",
      "title": "[스토리 제목]",
      "description": "As a [user], I want [feature] so that [benefit]",
      "acceptanceCriteria": ["기준1", "기준2", "Typecheck passes"],
      "priority": 1,
      "passes": false,
      "notes": ""
    }
  ]
}
```

### 변환 규칙
- 각 User Story → 하나의 JSON 항목
- ID: 순차적 (US-001, US-002, ...)
- priority: 의존성 순서 기반 (DB → 백엔드 → UI)
- 모든 스토리: `passes: false`, `notes: ""`
- branchName: `ralph/` 접두사 + kebab-case
- 모든 스토리에 "Typecheck passes" 추가
- UI 스토리에 "Verify in browser using dev-browser skill" 추가

### 스토리 크기 검증
각 스토리가 한 번의 반복에서 완료 가능한지 확인:
- ✅ DB 컬럼 추가 + 마이그레이션
- ✅ 기존 페이지에 UI 컴포넌트 추가
- ✅ 서버 액션에 로직 추가
- ❌ "전체 대시보드 구축" → 분할 필요

### 아카이브 규칙
새 prd.json 작성 전, 기존 파일의 branchName이 다르면:
1. `scripts/ralph/archive/YYYY-MM-DD-feature-name/` 생성
2. 기존 prd.json, progress.txt 복사
3. progress.txt 초기화

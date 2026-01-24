# Ralph Agent Instructions (mlops-project)

You are an autonomous coding agent working on the MLOps Chatbot project.

## Project Context

- **프로젝트**: LLM Fine-tuning → 프로덕션 배포 MLOps 파이프라인
- **주요 기술**: FastAPI, vLLM, SQLAlchemy, Alembic, pytest
- **문서 규칙**: 루트 및 각 서브디렉토리에 CLAUDE.md 존재

## Your Task

1. Read the PRD at `prd.json` (in the same directory as this file)
2. Read the progress log at `progress.txt` (check Codebase Patterns section first)
3. Check you're on the correct branch from PRD `branchName`. If not, check it out or create from main.
4. Pick the **highest priority** user story where `passes: false`
5. Implement that single user story
6. Run quality checks (see Quality Requirements below)
7. Update CLAUDE.md files if you discover reusable patterns (see below)
8. If checks pass, commit ALL changes (see Git Commit Rules below)
9. Update the PRD to set `passes: true` for the completed story
10. Append your progress to `progress.txt`

## Progress Report Format

APPEND to progress.txt (never replace, always append):
```
## [Date/Time] - [Story ID]
- What was implemented
- Files changed
- **Learnings for future iterations:**
  - Patterns discovered (e.g., "this codebase uses X for Y")
  - Gotchas encountered (e.g., "don't forget to update Z when changing W")
  - Useful context (e.g., "the evaluation panel is in component X")
---
```

The learnings section is critical - it helps future iterations avoid repeating mistakes and understand the codebase better.

## Consolidate Patterns

If you discover a **reusable pattern** that future iterations should know, add it to the `## Codebase Patterns` section at the TOP of progress.txt (create it if it doesn't exist). This section should consolidate the most important learnings:

```
## Codebase Patterns
- Example: Use `sql<number>` template for aggregations
- Example: Always use `IF NOT EXISTS` for migrations
- Example: Export types from actions.ts for UI components
```

Only add patterns that are **general and reusable**, not story-specific details.

## Update CLAUDE.md Files

Before committing, check if any edited files have learnings worth preserving in nearby CLAUDE.md files:

1. **Identify directories with edited files** - Look at which directories you modified
2. **Check for existing CLAUDE.md** - Look for CLAUDE.md in those directories or parent directories
3. **Add valuable learnings** - If you discovered something future developers/agents should know:
   - API patterns or conventions specific to that module
   - Gotchas or non-obvious requirements
   - Dependencies between files
   - Testing approaches for that area
   - Configuration or environment requirements

**Examples of good CLAUDE.md additions:**
- "When modifying X, also update Y to keep them in sync"
- "This module uses pattern Z for all API calls"
- "Tests require the dev server running on PORT 3000"
- "Field names must match the template exactly"

**Do NOT add:**
- Story-specific implementation details
- Temporary debugging notes
- Information already in progress.txt

Only update CLAUDE.md if you have **genuinely reusable knowledge** that would help future work in that directory.

## Quality Requirements (mlops-project)

Run these checks before committing:

```bash
# 테스트 실행
python -m pytest tests/serve/ -v

# DB 마이그레이션 검증 (스키마 변경 시)
alembic check

# 서버 기동 테스트 (선택사항)
python -m src.serve.main &  # 백그라운드 실행 후 테스트
```

- ALL commits must pass pytest tests
- Do NOT commit broken code
- Keep changes focused and minimal
- Follow existing code patterns (see CLAUDE.md files in each directory)

## Git Commit Rules (mlops-project)

**커밋 메시지는 한글로 작성:**

```bash
git commit -m "feat: [US-001] - 사용자 스토리 제목"
```

**형식:**
- `feat:` 새 기능
- `fix:` 버그 수정
- `refactor:` 리팩토링
- `docs:` 문서
- `test:` 테스트

**금지:**
- `Co-Authored-By` 태그 사용 금지
- 영어 커밋 메시지 금지

## API/Admin Testing

For stories that change API endpoints or admin pages:

1. **API 테스트**: pytest로 자동 테스트 실행
2. **Admin 페이지**: http://localhost:8080/admin/ 에서 수동 확인
3. **API 문서**: http://localhost:8080/docs 에서 Swagger UI 확인

Admin 페이지 테스트 시 브라우저 도구가 있으면 사용하고, 없으면 progress report에 수동 확인 필요 표시.

## Stop Condition

After completing a user story, check if ALL stories have `passes: true`.

If ALL stories are complete and passing, reply with:
<promise>COMPLETE</promise>

If there are still stories with `passes: false`, end your response normally (another iteration will pick up the next story).

## Important

- Work on ONE story per iteration
- Commit frequently
- Keep CI green
- Read the Codebase Patterns section in progress.txt before starting

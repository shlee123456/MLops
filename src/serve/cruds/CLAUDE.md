# src/serve/cruds/ - CRUD 함수

> **상위 문서**: [src/serve/CLAUDE.md](../CLAUDE.md) 참조

## 목적
데이터베이스 CRUD (Create, Read, Update, Delete) 작업 함수

## 파일 구조
| 파일 | 설명 |
|------|------|
| `chat.py` | Chat, Message CRUD 함수 |

## 로컬 규칙

### 함수 시그니처
- 첫 번째 인자: `db: AsyncSession`
- 반환 타입 명시
- async 함수로 작성

```python
async def get_chat(db: AsyncSession, chat_id: str) -> Optional[Chat]:
    ...
```

### 네이밍 컨벤션
- 생성: `create_*`
- 조회 (단일): `get_*`
- 조회 (복수): `get_*s` 또는 `list_*`
- 수정: `update_*`
- 삭제: `delete_*`

### 쿼리 작성
- `select()` 문 사용 (SQLAlchemy 2.0 스타일)
- N+1 방지: `selectinload()` 로 관계 로드
- 페이지네이션: `offset()`, `limit()` 사용

```python
stmt = (
    select(Chat)
    .options(selectinload(Chat.messages))
    .offset(skip)
    .limit(limit)
)
```

## 주요 함수

### chat.py
| 함수 | 설명 |
|------|------|
| `create_chat()` | 채팅 세션 생성 |
| `get_chat()` | ID로 채팅 조회 |
| `get_chats()` | 채팅 목록 조회 (페이지네이션) |
| `delete_chat()` | 채팅 삭제 |
| `add_message()` | 메시지 추가 |
| `get_messages()` | 채팅의 메시지 목록 조회 |

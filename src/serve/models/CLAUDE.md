# src/serve/models/ - ORM 모델

> **상위 문서**: [src/serve/CLAUDE.md](../CLAUDE.md) 참조

## 목적
SQLAlchemy ORM 모델 정의 (데이터베이스 스키마)

## 파일 구조
| 파일 | 설명 |
|------|------|
| `models.py` | Chat, Message, LLMConfig 모델 |

## 모델 관계
```
LLMConfig (독립)

Chat (1) ──< Message (N)
```

## 로컬 규칙

### 모델 정의
- `Base` 클래스 상속 (`from ..database import Base`)
- `Mapped[]` 타입 힌트 사용 (SQLAlchemy 2.0 스타일)
- `mapped_column()` 으로 컬럼 정의
- 타임스탬프는 `server_default=func.now()` 사용

### 네이밍 컨벤션
- 테이블명: 복수형 스네이크 케이스 (`chats`, `messages`)
- 클래스명: 단수형 파스칼 케이스 (`Chat`, `Message`)
- 외래키: `{참조테이블}_id` 형식 (`chat_id`)

### 모델 추가 시
1. `models.py`에 클래스 정의
2. `__init__.py`에 export 추가
3. Alembic 마이그레이션 생성: `alembic revision --autogenerate -m "Add X"`
4. 마이그레이션 적용: `alembic upgrade head`

## 주요 모델

### Chat
- `id`: UUID 문자열 (자동 생성)
- `title`: 채팅 제목
- `model`: 사용 모델명
- `messages`: Message 관계 (cascade delete)

### Message
- `role`: system / user / assistant
- `content`: 메시지 내용
- `*_tokens`: 토큰 사용량 (선택)

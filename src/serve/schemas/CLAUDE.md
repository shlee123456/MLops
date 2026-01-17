# src/serve/schemas/ - Pydantic 스키마

> **상위 문서**: [src/serve/CLAUDE.md](../CLAUDE.md) 참조

## 목적
API 요청/응답 데이터 검증 및 직렬화 (Pydantic 모델)

## 파일 구조
| 파일 | 설명 |
|------|------|
| `common.py` | 공통 스키마 (Health, Error) |
| `chat.py` | 채팅 관련 스키마 |
| `completion.py` | 텍스트 완성 스키마 |

## 로컬 규칙

### 스키마 정의
- `BaseModel` 상속
- `Field()` 로 검증 규칙 및 설명 추가
- 선택 필드는 `Optional[]` + `None` 기본값

### 네이밍 컨벤션
- 요청: `*Request` (예: `ChatCompletionRequest`)
- 응답: `*Response` (예: `ChatCompletionResponse`)
- ORM 변환용: `Config.from_attributes = True`

### ORM 모델 vs Pydantic 스키마
```python
# ORM (models/) - DB 저장용
class Chat(Base):
    __tablename__ = "chats"

# Pydantic (schemas/) - API 검증용
class ChatResponse(BaseModel):
    class Config:
        from_attributes = True
```

## 주요 스키마

### chat.py
- `Message`: role + content
- `ChatCompletionRequest`: messages, temperature, max_tokens, stream
- `ChatCompletionResponse`: content, model, usage, session_id
- `ChatCreate`, `ChatResponse`, `MessageResponse`

### completion.py
- `CompletionRequest`: prompt, temperature, max_tokens
- `CompletionResponse`: content, model, usage

### common.py
- `HealthResponse`: status, vllm_connected, available_models
- `ErrorResponse`: error, detail, status_code

# src/serve/routers/ - API 라우터

> **상위 문서**: [src/serve/CLAUDE.md](../CLAUDE.md) 참조

## 목적
FastAPI 라우터 및 엔드포인트 정의

## 파일 구조
| 파일 | 설명 |
|------|------|
| `router.py` | 모든 라우터 통합 |
| `dependency.py` | 의존성 주입 함수 |
| `health.py` | `/`, `/health`, `/metrics` |
| `models.py` | `/v1/models` |
| `chat.py` | `/v1/chat/completions`, `/v1/chats/*` |
| `completion.py` | `/v1/completions` |

## 로컬 규칙

### 라우터 정의
```python
router = APIRouter(prefix="/v1", tags=["Chat"])

@router.post("/chat/completions")
async def chat_completion(...):
    ...
```

### 의존성 주입 (dependency.py)
- `verify_api_key`: API 키 검증
- `get_db_session`: DB 세션 제공
- `get_llm_client`: vLLM 클라이언트 제공

```python
@router.post("/endpoint")
async def endpoint(
    authenticated: bool = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
    vllm_client = Depends(get_llm_client),
):
```

### 에러 처리
- `HTTPException` 사용
- 503: 서비스 불가 (vLLM 연결 실패)
- 404: 리소스 없음
- 401: 인증 실패
- 500: 내부 오류

### 새 엔드포인트 추가 시
1. 해당 도메인 라우터 파일에 추가 (또는 새 파일 생성)
2. `router.py`에 include_router 추가
3. 스키마 필요 시 `schemas/`에 추가
4. CRUD 필요 시 `cruds/`에 추가

## API 엔드포인트 목록

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | API 정보 |
| GET | `/health` | 헬스 체크 |
| GET | `/metrics` | 메트릭 |
| GET | `/v1/models` | 모델 목록 |
| POST | `/v1/chat/completions` | 채팅 완성 |
| POST | `/v1/completions` | 텍스트 완성 |
| POST | `/v1/chats` | 채팅 세션 생성 |
| GET | `/v1/chats` | 채팅 목록 |
| GET | `/v1/chats/{id}` | 채팅 조회 |
| DELETE | `/v1/chats/{id}` | 채팅 삭제 |
| GET | `/v1/chats/{id}/messages` | 메시지 목록 |

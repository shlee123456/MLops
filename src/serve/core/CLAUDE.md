# src/serve/core/ - 핵심 설정 및 클라이언트

> **상위 문서**: [src/serve/CLAUDE.md](../CLAUDE.md) 참조

## 목적
애플리케이션 설정 및 외부 서비스 클라이언트 관리

## 파일 구조
| 파일 | 설명 |
|------|------|
| `config.py` | pydantic-settings 기반 환경 설정 |
| `llm.py` | vLLM 클라이언트 싱글턴 래퍼 |

## 로컬 규칙

### config.py
- `Settings` 클래스는 `BaseSettings` 상속
- 환경 변수는 `.env` 파일에서 자동 로드
- `@lru_cache`로 settings 인스턴스 캐싱
- 새 설정 추가 시 기본값 필수 지정

```python
# 설정 사용 예시
from src.serve.core.config import settings
print(settings.vllm_base_url)
```

### llm.py
- `init_vllm_client()`: 앱 시작 시 호출
- `get_vllm_client()`: 의존성 주입에서 사용
- `close_vllm_client()`: 앱 종료 시 호출

## 환경 변수
| 변수 | 기본값 | 설명 |
|------|--------|------|
| `FASTAPI_HOST` | 0.0.0.0 | 서버 호스트 |
| `FASTAPI_PORT` | 8080 | 서버 포트 |
| `VLLM_BASE_URL` | http://localhost:8000/v1 | vLLM 서버 URL |
| `ENABLE_AUTH` | false | 인증 활성화 |
| `API_KEY` | your-secret-api-key | API 키 |
| `DATABASE_URL` | sqlite+aiosqlite:///./mlops_chat.db | DB 연결 |

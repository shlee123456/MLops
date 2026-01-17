# src/serve/ - 서빙 파이프라인

> **상위 문서**: [/CLAUDE.md](../../CLAUDE.md) - 프로젝트 전체 규칙, 환경변수, 세션 히스토리/터미널 로그 기록 방법 참조

vLLM 기반 고성능 추론 + FastAPI 래퍼

## 파일

| 파일 | 설명 |
|------|------|
| `01_vllm_server.py` | vLLM OpenAI 호환 서버 |
| `02_vllm_client.py` | VLLMClient 클래스 |
| `03_gradio_vllm_demo.py` | Gradio UI |
| `04_fastapi_server.py` | FastAPI 래퍼 (인증, 로깅) |
| `05_prompt_templates.py` | 프롬프트 템플릿 |
| `06_benchmark_vllm.py` | 벤치마크 |
| `07_langchain_pipeline.py` | LangChain 통합 |

## 실행 순서

```bash
# 1. vLLM 서버 먼저
python src/serve/01_vllm_server.py  # :8000

# 2. FastAPI 래퍼 (vLLM 필요)
python src/serve/04_fastapi_server.py  # :8080

# 또는 Docker
docker-compose up vllm-server fastapi-server
```

## API 엔드포인트

| 서비스 | 포트 | 엔드포인트 |
|--------|------|------------|
| vLLM | 8000 | `POST /v1/chat/completions`, `/v1/completions` |
| FastAPI | 8080 | 위 + `GET /health`, `/metrics` |

## VLLMClient 사용

```python
from serve.vllm_client import VLLMClient
# 또는
from src.serve.vllm_client import VLLMClient

client = VLLMClient(base_url="http://localhost:8000")

# 동기 호출
response = client.chat(messages=[{"role": "user", "content": "Hello"}])

# 스트리밍
async for chunk in client.chat_stream(messages):
    print(chunk)
```

## Pydantic 모델

```python
class ChatCompletionRequest(BaseModel):
    messages: List[Message] = Field(..., description="대화 메시지")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(512, ge=1, le=4096)
    stream: bool = Field(False)
```

## 스트리밍 (SSE)

```python
async def stream_generator():
    async for chunk in client.chat_stream(messages):
        yield f"data: {json.dumps(chunk)}\n\n"

return StreamingResponse(stream_generator(), media_type="text/event-stream")
```

## vLLM 최적화 옵션

```bash
--gpu-memory-utilization 0.9
--max-model-len 4096
--tensor-parallel-size 2      # 멀티 GPU
--quantization awq            # AWQ 양자화
```

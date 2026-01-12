#!/usr/bin/env python3
"""
Phase 3-4: FastAPI Server Wrapper

vLLM 서버를 래핑하는 커스텀 FastAPI 서버
인증, 로깅, 모니터링 등 추가 기능 제공
"""

import os
import time
import logging
from datetime import datetime
from typing import List, Dict, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# 상대 경로 임포트
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from serve.vllm_client import VLLMClient
except ImportError:
    from vllm_client import VLLMClient

load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================
# Pydantic Models
# ============================================================

class Message(BaseModel):
    """채팅 메시지"""
    role: str = Field(..., description="메시지 역할 (system/user/assistant)")
    content: str = Field(..., description="메시지 내용")


class ChatCompletionRequest(BaseModel):
    """채팅 완성 요청"""
    messages: List[Message] = Field(..., description="대화 메시지 리스트")
    model: Optional[str] = Field(None, description="모델 이름 (생략 시 기본값)")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="샘플링 온도")
    max_tokens: int = Field(512, ge=1, le=4096, description="최대 생성 토큰")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Top-p 샘플링")
    stream: bool = Field(False, description="스트리밍 모드")


class ChatCompletionResponse(BaseModel):
    """채팅 완성 응답"""
    content: str = Field(..., description="생성된 텍스트")
    model: str = Field(..., description="사용된 모델")
    usage: Dict = Field(..., description="토큰 사용량")
    finish_reason: Optional[str] = Field(None, description="완료 이유")
    created_at: str = Field(..., description="생성 시각")


class CompletionRequest(BaseModel):
    """텍스트 완성 요청"""
    prompt: str = Field(..., description="프롬프트 텍스트")
    model: Optional[str] = Field(None, description="모델 이름")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(512, ge=1, le=4096)


class HealthResponse(BaseModel):
    """헬스 체크 응답"""
    status: str
    vllm_connected: bool
    available_models: List[str]
    timestamp: str


# ============================================================
# FastAPI App
# ============================================================

# 전역 vLLM 클라이언트
vllm_client: Optional[VLLMClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    global vllm_client

    # Startup
    logger.info("Starting FastAPI server...")

    vllm_base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
    try:
        vllm_client = VLLMClient(base_url=vllm_base_url)
        if vllm_client.health_check():
            logger.info(f"✓ Connected to vLLM server: {vllm_base_url}")
        else:
            logger.warning(f"⚠ vLLM server not responding: {vllm_base_url}")
    except Exception as e:
        logger.error(f"✗ Failed to connect to vLLM: {e}")

    yield

    # Shutdown
    logger.info("Shutting down FastAPI server...")


app = FastAPI(
    title="MLOps Chatbot API",
    description="FastAPI wrapper for vLLM inference server with authentication and monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# Authentication (Simple API Key)
# ============================================================

API_KEY = os.getenv("API_KEY", "your-secret-api-key")


async def verify_api_key(x_api_key: str = Header(None)):
    """API 키 검증"""
    if os.getenv("ENABLE_AUTH", "false").lower() == "true":
        if x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True


# ============================================================
# Endpoints
# ============================================================

@app.get("/", tags=["Info"])
async def root():
    """루트 엔드포인트"""
    return {
        "name": "MLOps Chatbot API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "models": "/v1/models",
            "chat": "/v1/chat/completions",
            "completion": "/v1/completions",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """헬스 체크"""
    if vllm_client is None:
        return HealthResponse(
            status="unhealthy",
            vllm_connected=False,
            available_models=[],
            timestamp=datetime.now().isoformat()
        )

    vllm_healthy = vllm_client.health_check()
    models = vllm_client.list_models() if vllm_healthy else []

    return HealthResponse(
        status="healthy" if vllm_healthy else "degraded",
        vllm_connected=vllm_healthy,
        available_models=models,
        timestamp=datetime.now().isoformat()
    )


@app.get("/v1/models", tags=["Models"])
async def list_models(authenticated: bool = Depends(verify_api_key)):
    """사용 가능한 모델 목록"""
    if vllm_client is None:
        raise HTTPException(status_code=503, detail="vLLM client not initialized")

    models = vllm_client.list_models()
    return {
        "object": "list",
        "data": [{"id": model, "object": "model"} for model in models]
    }


@app.post("/v1/chat/completions", tags=["Chat"])
async def chat_completion(
    request: ChatCompletionRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """채팅 완성"""
    if vllm_client is None:
        raise HTTPException(status_code=503, detail="vLLM client not initialized")

    start_time = time.time()

    try:
        # 메시지 변환
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # 스트리밍 모드
        if request.stream:
            async def generate():
                stream = vllm_client.chat_completion(
                    messages=messages,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    top_p=request.top_p,
                    stream=True
                )

                for chunk in stream:
                    yield f"data: {chunk}\n\n"

                yield "data: [DONE]\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")

        # 일반 모드
        response = vllm_client.chat_completion(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            stream=False
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        elapsed_time = time.time() - start_time

        # 로깅
        logger.info(
            f"Chat completion - Model: {response['model']}, "
            f"Tokens: {response['usage'].get('total_tokens', 'N/A')}, "
            f"Time: {elapsed_time:.2f}s"
        )

        return ChatCompletionResponse(
            content=response["content"],
            model=response["model"],
            usage=response["usage"],
            finish_reason=response.get("finish_reason"),
            created_at=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/completions", tags=["Completion"])
async def completion(
    request: CompletionRequest,
    authenticated: bool = Depends(verify_api_key)
):
    """텍스트 완성"""
    if vllm_client is None:
        raise HTTPException(status_code=503, detail="vLLM client not initialized")

    start_time = time.time()

    try:
        response = vllm_client.completion(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        elapsed_time = time.time() - start_time

        logger.info(
            f"Completion - Model: {response['model']}, "
            f"Tokens: {response['usage'].get('total_tokens', 'N/A')}, "
            f"Time: {elapsed_time:.2f}s"
        )

        return {
            "content": response["content"],
            "model": response["model"],
            "usage": response["usage"],
            "created_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error in completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Monitoring Endpoints
# ============================================================

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus 메트릭 (간단한 버전)"""
    # 실제 프로덕션에서는 prometheus_client 사용
    return {
        "requests_total": "TODO",
        "request_duration_seconds": "TODO",
        "errors_total": "TODO"
    }


# ============================================================
# Main
# ============================================================

def main():
    """메인 실행 함수"""
    import uvicorn

    print("\n" + "="*60)
    print("  FastAPI Server for vLLM")
    print("="*60 + "\n")

    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", "8080"))

    print(f"Server Configuration:")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  vLLM URL: {os.getenv('VLLM_BASE_URL', 'http://localhost:8000/v1')}")
    print(f"  Authentication: {os.getenv('ENABLE_AUTH', 'false')}")

    if os.getenv("ENABLE_AUTH", "false").lower() == "true":
        print(f"  API Key: {API_KEY}")

    print(f"\nAPI Documentation:")
    print(f"  Swagger UI: http://{host}:{port}/docs")
    print(f"  ReDoc: http://{host}:{port}/redoc")

    print("\n" + "="*60 + "\n")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    main()

"""Health and info endpoints"""

from datetime import datetime

from fastapi import APIRouter

from ..core.config import settings
from ..core.llm import get_vllm_client
from ..schemas.common import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "models": "/v1/models",
            "chat": "/v1/chat/completions",
            "completion": "/v1/completions",
            "chats": "/v1/chats",
            "docs": "/docs",
        }
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    vllm_client = get_vllm_client()

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


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint (placeholder)"""
    return {
        "requests_total": "TODO",
        "request_duration_seconds": "TODO",
        "errors_total": "TODO"
    }

#!/usr/bin/env python3
"""
FastAPI Server with Clean Architecture

vLLM 서버를 래핑하는 커스텀 FastAPI 서버
인증, 로깅, 모니터링, 채팅 히스토리 저장 기능 제공
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .core.llm import init_vllm_client, close_vllm_client
from .database import init_db, close_db
from .routers import api_router

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting FastAPI server...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Initialize vLLM client
    init_vllm_client()

    yield

    # Shutdown
    logger.info("Shutting down FastAPI server...")
    close_vllm_client()
    await close_db()


app = FastAPI(
    title=settings.app_name,
    description="FastAPI wrapper for vLLM inference server with authentication and monitoring",
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)


def main():
    """Main entry point"""
    import uvicorn

    print("\n" + "=" * 60)
    print("  FastAPI Server for vLLM (Clean Architecture)")
    print("=" * 60 + "\n")

    print("Server Configuration:")
    print(f"  Host: {settings.fastapi_host}")
    print(f"  Port: {settings.fastapi_port}")
    print(f"  vLLM URL: {settings.vllm_base_url}")
    print(f"  Authentication: {settings.enable_auth}")
    print(f"  Database: {settings.database_url}")

    if settings.enable_auth:
        print(f"  API Key: {settings.api_key}")

    print(f"\nAPI Documentation:")
    print(f"  Swagger UI: http://{settings.fastapi_host}:{settings.fastapi_port}/docs")
    print(f"  ReDoc: http://{settings.fastapi_host}:{settings.fastapi_port}/redoc")

    print("\n" + "=" * 60 + "\n")

    uvicorn.run(
        "src.serve.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )


if __name__ == "__main__":
    main()

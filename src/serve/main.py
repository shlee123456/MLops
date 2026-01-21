"""
FastAPI Application Entry Point

클린 아키텍처 기반 FastAPI 서버
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.serve.core.config import settings
from src.serve.admin import create_admin
from src.serve.core.metrics import PrometheusMiddleware
from src.serve.core.logging import setup_logging, get_logger, RequestLoggingMiddleware
from src.serve.database import init_db, close_db
from src.serve.routers import router
from src.serve.routers.dependency import close_llm_client

# structlog 기반 로깅 설정
# 프로덕션에서는 json_format=True, 개발에서는 False
setup_logging(log_dir=settings.log_dir, json_format=not settings.debug)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 생명주기 관리"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"vLLM URL: {settings.vllm_base_url}")
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"Authentication: {'enabled' if settings.enable_auth else 'disabled'}")
    
    # DB 초기화 (개발용 - 프로덕션에서는 Alembic 사용)
    if settings.debug:
        await init_db()
        logger.info("Database tables created (debug mode)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await close_llm_client()
    await close_db()
    logger.info("Shutdown complete")


# FastAPI 앱 생성
app = FastAPI(
    title=settings.app_name,
    description="vLLM 기반 LLM 서빙 API with Clean Architecture",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Request 로깅 미들웨어 (structlog)
app.add_middleware(RequestLoggingMiddleware)

# Prometheus 메트릭 미들웨어
app.add_middleware(PrometheusMiddleware)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session 미들웨어는 SQLAdmin이 자체적으로 추가함 (AuthenticationBackend에서)

# SQLAdmin 마운트
admin = create_admin(app)
logger.info("Admin UI: /admin")

# 라우터 등록
app.include_router(router)


def main():
    """개발 서버 실행"""
    import uvicorn
    
    print("\n" + "=" * 60)
    print(f"  {settings.app_name} v{settings.app_version}")
    print("=" * 60 + "\n")
    
    print("Server Configuration:")
    print(f"  Host: {settings.fastapi_host}")
    print(f"  Port: {settings.fastapi_port}")
    print(f"  vLLM URL: {settings.vllm_base_url}")
    print(f"  Database: {settings.database_url}")
    print(f"  Debug: {settings.debug}")
    print(f"  Auth: {'enabled' if settings.enable_auth else 'disabled'}")
    
    print("\nAPI Documentation:")
    print(f"  Swagger UI: http://localhost:{settings.fastapi_port}/docs")
    print(f"  ReDoc: http://localhost:{settings.fastapi_port}/redoc")
    print(f"  Admin UI: http://localhost:{settings.fastapi_port}/admin")
    
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

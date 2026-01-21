"""
Test Fixtures

테스트용 픽스처 정의
"""

import asyncio
import os
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# 테스트용 DB 파일 경로 (프로젝트 루트 기준)
TEST_DB_PATH = "/tmp/test_mlops_chat.db"
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
TEST_SYNC_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"


# 환경변수 설정 (테스트 모듈 로드 전에)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


from src.serve.database import Base
from src.serve.routers.dependency import get_db, get_llm_client
from src.serve.core.llm import LLMClient


@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 픽스처"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """테스트 세션 시작 전 테스트 DB 설정"""
    # 기존 테스트 DB 삭제
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    # 동기 엔진으로 테이블 생성
    sync_engine = create_engine(TEST_SYNC_DATABASE_URL, echo=False)
    Base.metadata.create_all(bind=sync_engine)
    sync_engine.dispose()

    yield

    # 테스트 후 DB 파일 삭제
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest_asyncio.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """테스트용 DB 세션"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Mock LLM 클라이언트"""
    client = MagicMock(spec=LLMClient)
    client.health_check = AsyncMock(return_value=True)
    client.list_models = AsyncMock(return_value=["test-model"])
    client.chat_completion = AsyncMock(return_value={
        "content": "테스트 응답입니다.",
        "model": "test-model",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30,
        },
        "finish_reason": "stop",
    })
    return client


@pytest_asyncio.fixture
async def client(test_db: AsyncSession, mock_llm_client: MagicMock) -> AsyncGenerator[AsyncClient, None]:
    """테스트용 HTTP 클라이언트"""
    from src.serve.main import app

    async def override_get_db():
        yield test_db

    def override_get_llm_client():
        return mock_llm_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm_client] = override_get_llm_client

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

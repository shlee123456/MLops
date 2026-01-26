"""
Alembic Migration Environment (Async)

비동기 SQLAlchemy 2.0 마이그레이션 설정
"""

import asyncio
import os
import sys
from logging.config import fileConfig
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(project_root))

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Alembic Config 객체
config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 모델 메타데이터 임포트
from src.serve.database import Base
from src.serve.models import ChatMessage, Conversation, FewshotMessage, LLMConfig, LLMModel, User  # noqa: F401

target_metadata = Base.metadata

# 환경변수에서 DB URL 가져오기 (alembic.ini 오버라이드)
def get_url():
    return os.getenv(
        "DATABASE_URL",
        config.get_main_option("sqlalchemy.url")
    )


def run_migrations_offline() -> None:
    """
    오프라인 마이그레이션 (SQL 스크립트 생성)
    
    실제 DB 연결 없이 SQL 스크립트를 생성합니다.
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """마이그레이션 실행"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """비동기 마이그레이션 실행"""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    온라인 마이그레이션 (DB 직접 연결)
    
    비동기 엔진을 사용하여 마이그레이션을 실행합니다.
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

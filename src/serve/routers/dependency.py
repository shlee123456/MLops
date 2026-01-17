"""FastAPI dependencies"""

from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..core.llm import get_vllm_client
from ..database import get_db


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """Verify API key if authentication is enabled"""
    if settings.enable_auth:
        if x_api_key != settings.api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
    return True


async def get_db_session() -> AsyncSession:
    """Get database session dependency"""
    async for session in get_db():
        yield session


def get_llm_client():
    """Get vLLM client dependency"""
    client = get_vllm_client()
    if client is None:
        raise HTTPException(status_code=503, detail="vLLM client not initialized")
    return client

"""
Application Configuration

pydantic-settings 기반 환경설정
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # 앱 설정
    app_name: str = "MLOps Chatbot API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 서버 설정
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8080
    
    # vLLM 설정
    vllm_base_url: str = "http://localhost:8000/v1"
    default_model: Optional[str] = None
    
    # 데이터베이스
    database_url: str = "sqlite+aiosqlite:///./mlops_chat.db"
    database_echo: bool = False
    
    # 인증
    enable_auth: bool = False
    api_key: str = "your-secret-api-key"
    
    # LLM 기본값
    default_temperature: float = 0.7
    default_max_tokens: int = 512
    default_top_p: float = 0.9
    
    # CORS
    cors_origins: list[str] = ["*"]

    # HuggingFace
    huggingface_token: Optional[str] = None

    # 로깅
    log_dir: str = "./logs/fastapi"  # 로컬: ./logs/fastapi, Docker: /logs


@lru_cache
def get_settings() -> Settings:
    """설정 싱글톤 반환"""
    return Settings()


# 전역 설정 인스턴스
settings = get_settings()

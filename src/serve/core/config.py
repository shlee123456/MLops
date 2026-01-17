"""Application configuration using pydantic-settings"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "MLOps Chatbot API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8080

    # vLLM
    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_timeout: int = 60

    # Authentication
    enable_auth: bool = False
    api_key: str = "your-secret-api-key"

    # Database
    database_url: str = "sqlite+aiosqlite:///./mlops_chat.db"

    # CORS
    cors_origins: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins string to list"""
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()

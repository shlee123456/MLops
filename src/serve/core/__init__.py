"""
Core Module

설정, LLM 클라이언트, 메트릭, 로깅
"""

from src.serve.core.config import settings
from src.serve.core.llm import LLMClient
from src.serve.core.metrics import (
    PrometheusMiddleware,
    get_metrics,
    record_llm_request,
    record_db_query,
)
from src.serve.core.logging import (
    setup_logging,
    get_logger,
    RequestLoggingMiddleware,
    request_id_var,
)
from src.serve.core.security import hash_password, verify_password

__all__ = [
    # Config
    "settings",
    # LLM
    "LLMClient",
    # Metrics
    "PrometheusMiddleware",
    "get_metrics",
    "record_llm_request",
    "record_db_query",
    # Logging
    "setup_logging",
    "get_logger",
    "RequestLoggingMiddleware",
    "request_id_var",
    # Security
    "hash_password",
    "verify_password",
]

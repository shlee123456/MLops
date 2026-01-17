"""Core module: Configuration and LLM client"""

from .config import settings
from .llm import get_vllm_client

__all__ = ["settings", "get_vllm_client"]

"""vLLM client singleton wrapper"""

import logging
from typing import Optional

from .config import settings

logger = logging.getLogger(__name__)

# Global vLLM client instance
_vllm_client: Optional["VLLMClient"] = None


def get_vllm_client() -> Optional["VLLMClient"]:
    """Get the global vLLM client instance"""
    return _vllm_client


def init_vllm_client() -> Optional["VLLMClient"]:
    """Initialize the global vLLM client"""
    global _vllm_client

    try:
        # Import VLLMClient from existing module
        import sys
        from pathlib import Path

        # Add parent directory to path for imports
        serve_dir = Path(__file__).parent.parent
        if str(serve_dir) not in sys.path:
            sys.path.insert(0, str(serve_dir))

        try:
            from serve.vllm_client import VLLMClient
        except ImportError:
            from vllm_client import VLLMClient

        _vllm_client = VLLMClient(
            base_url=settings.vllm_base_url,
            timeout=settings.vllm_timeout
        )

        if _vllm_client.health_check():
            logger.info(f"Connected to vLLM server: {settings.vllm_base_url}")
        else:
            logger.warning(f"vLLM server not responding: {settings.vllm_base_url}")

        return _vllm_client

    except Exception as e:
        logger.error(f"Failed to connect to vLLM: {e}")
        return None


def close_vllm_client() -> None:
    """Close the vLLM client connection"""
    global _vllm_client
    _vllm_client = None
    logger.info("vLLM client closed")

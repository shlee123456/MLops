"""Common schemas for health and errors"""

from typing import List, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    vllm_connected: bool
    available_models: List[str]
    timestamp: str


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: Optional[str] = None
    status_code: int = 500

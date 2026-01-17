"""Completion-related schemas"""

from datetime import datetime
from typing import Dict, Optional
from pydantic import BaseModel, Field


class CompletionRequest(BaseModel):
    """Text completion request"""
    prompt: str = Field(..., description="Prompt text")
    model: Optional[str] = Field(None, description="Model name")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(512, ge=1, le=4096, description="Maximum tokens to generate")


class CompletionResponse(BaseModel):
    """Text completion response"""
    content: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used")
    usage: Dict = Field(..., description="Token usage")
    created_at: str = Field(..., description="Creation timestamp")

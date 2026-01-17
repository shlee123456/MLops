"""Chat-related schemas"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    """Chat message"""
    role: str = Field(..., description="Message role (system/user/assistant)")
    content: str = Field(..., description="Message content")


class ChatCompletionRequest(BaseModel):
    """Chat completion request"""
    messages: List[Message] = Field(..., description="Conversation messages")
    model: Optional[str] = Field(None, description="Model name (uses default if omitted)")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(512, ge=1, le=4096, description="Maximum tokens to generate")
    top_p: float = Field(0.9, ge=0.0, le=1.0, description="Top-p sampling")
    stream: bool = Field(False, description="Enable streaming mode")
    session_id: Optional[str] = Field(None, description="Chat session ID for persistence")


class ChatCompletionResponse(BaseModel):
    """Chat completion response"""
    content: str = Field(..., description="Generated text")
    model: str = Field(..., description="Model used")
    usage: Dict = Field(..., description="Token usage")
    finish_reason: Optional[str] = Field(None, description="Completion finish reason")
    created_at: str = Field(..., description="Creation timestamp")
    session_id: Optional[str] = Field(None, description="Chat session ID")


class ChatCreate(BaseModel):
    """Create chat session request"""
    title: Optional[str] = Field(None, description="Chat title")
    model: Optional[str] = Field(None, description="Default model for this chat")


class ChatResponse(BaseModel):
    """Chat session response"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: Optional[str]
    model: Optional[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class MessageResponse(BaseModel):
    """Message response"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    chat_id: str
    role: str
    content: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    finish_reason: Optional[str] = None
    created_at: datetime

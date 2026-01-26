"""
Chat Models - 대화 기록 ORM 모델
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, Integer, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.serve.database import Base


class LLMConfig(Base):
    """LLM 설정 프리셋"""
    __tablename__ = "llm_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    llm_model_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("llm_models.id"), nullable=True
    )
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.7, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=512, nullable=False)
    top_p: Mapped[float] = mapped_column(Float, default=0.9, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # 관계
    llm_model: Mapped[Optional["LLMModel"]] = relationship(
        "LLMModel", back_populates="configs"
    )
    conversations: Mapped[list["Conversation"]] = relationship(
        "Conversation", back_populates="llm_config"
    )
    fewshot_messages: Mapped[list["FewshotMessage"]] = relationship(
        "FewshotMessage", back_populates="llm_config", cascade="all, delete-orphan",
        order_by="FewshotMessage.order"
    )

    def __repr__(self) -> str:
        return f"<LLMConfig(id={self.id}, name={self.name})>"


class Conversation(Base):
    """대화 세션"""
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    llm_config_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("llm_configs.id"), nullable=True
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    session_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 관계
    llm_config: Mapped[Optional["LLMConfig"]] = relationship(
        "LLMConfig", back_populates="conversations"
    )
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="conversations"
    )
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, title={self.title})>"


class ChatMessage(Base):
    """개별 채팅 메시지"""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # system/user/assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 메타데이터
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tokens_used: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    extra_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # TTFT (Time To First Token) 측정
    first_token_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # 관계
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="messages"
    )

    @property
    def ttft_ms(self) -> Optional[int]:
        """TTFT (Time To First Token) 계산 - 밀리초 단위"""
        if self.first_token_at is None or self.created_at is None:
            return None
        delta = self.first_token_at - self.created_at
        return int(delta.total_seconds() * 1000)

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, role={self.role})>"


class FewshotMessage(Base):
    """Few-shot 예시 메시지 - LLM 설정에 포함되는 예시 대화"""
    __tablename__ = "fewshot_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    llm_config_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("llm_configs.id"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user/assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # 관계
    llm_config: Mapped["LLMConfig"] = relationship(
        "LLMConfig", back_populates="fewshot_messages"
    )

    def __repr__(self) -> str:
        return f"<FewshotMessage(id={self.id}, llm_config_id={self.llm_config_id}, role={self.role})>"

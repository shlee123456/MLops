"""
LLM Model - LLM 엔드포인트 관리 ORM 모델
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, Integer, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.serve.database import Base

if TYPE_CHECKING:
    from src.serve.models.chat import LLMConfig


class LLMModel(Base):
    """LLM 엔드포인트 정보"""
    __tablename__ = "llm_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    api_url: Mapped[str] = mapped_column(String(500), nullable=False)
    api_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_tokens_limit: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # 관계
    configs: Mapped[list["LLMConfig"]] = relationship(
        "LLMConfig", back_populates="llm_model"
    )

    def __repr__(self) -> str:
        return f"<LLMModel(id={self.id}, name={self.name}, api_url={self.api_url})>"

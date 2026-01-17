"""CRUD operations for Chat and Message"""

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.models import Chat, Message


async def create_chat(
    db: AsyncSession,
    title: Optional[str] = None,
    model: Optional[str] = None,
) -> Chat:
    """Create a new chat session"""
    chat = Chat(title=title, model=model)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


async def get_chat(
    db: AsyncSession,
    chat_id: str,
    include_messages: bool = True,
) -> Optional[Chat]:
    """Get a chat by ID"""
    if include_messages:
        stmt = (
            select(Chat)
            .where(Chat.id == chat_id)
            .options(selectinload(Chat.messages))
        )
    else:
        stmt = select(Chat).where(Chat.id == chat_id)

    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_chats(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Chat]:
    """Get all chats with pagination"""
    stmt = (
        select(Chat)
        .options(selectinload(Chat.messages))
        .order_by(Chat.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()


async def delete_chat(db: AsyncSession, chat_id: str) -> bool:
    """Delete a chat and its messages"""
    chat = await get_chat(db, chat_id, include_messages=False)
    if chat:
        await db.delete(chat)
        await db.commit()
        return True
    return False


async def add_message(
    db: AsyncSession,
    chat_id: str,
    role: str,
    content: str,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    finish_reason: Optional[str] = None,
) -> Message:
    """Add a message to a chat"""
    message = Message(
        chat_id=chat_id,
        role=role,
        content=content,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        finish_reason=finish_reason,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_messages(
    db: AsyncSession,
    chat_id: str,
    skip: int = 0,
    limit: int = 100,
) -> Sequence[Message]:
    """Get messages for a chat"""
    stmt = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()

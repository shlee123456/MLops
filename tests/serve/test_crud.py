"""Tests for CRUD operations"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.serve.cruds import chat as chat_crud


@pytest.mark.asyncio
async def test_create_chat(test_db: AsyncSession):
    """Test creating a chat session"""
    chat = await chat_crud.create_chat(
        db=test_db,
        title="Test Chat",
        model="test-model",
    )

    assert chat.id is not None
    assert chat.title == "Test Chat"
    assert chat.model == "test-model"


@pytest.mark.asyncio
async def test_get_chat(test_db: AsyncSession):
    """Test getting a chat by ID"""
    # Create a chat
    chat = await chat_crud.create_chat(db=test_db, title="Test Chat")

    # Get the chat
    retrieved = await chat_crud.get_chat(db=test_db, chat_id=chat.id)

    assert retrieved is not None
    assert retrieved.id == chat.id
    assert retrieved.title == "Test Chat"


@pytest.mark.asyncio
async def test_get_chat_not_found(test_db: AsyncSession):
    """Test getting a non-existent chat"""
    retrieved = await chat_crud.get_chat(db=test_db, chat_id="non-existent-id")
    assert retrieved is None


@pytest.mark.asyncio
async def test_get_chats(test_db: AsyncSession):
    """Test getting all chats"""
    # Create multiple chats
    await chat_crud.create_chat(db=test_db, title="Chat 1")
    await chat_crud.create_chat(db=test_db, title="Chat 2")
    await chat_crud.create_chat(db=test_db, title="Chat 3")

    # Get all chats
    chats = await chat_crud.get_chats(db=test_db)

    assert len(chats) == 3


@pytest.mark.asyncio
async def test_delete_chat(test_db: AsyncSession):
    """Test deleting a chat"""
    # Create a chat
    chat = await chat_crud.create_chat(db=test_db, title="To Delete")

    # Delete it
    deleted = await chat_crud.delete_chat(db=test_db, chat_id=chat.id)
    assert deleted is True

    # Verify it's gone
    retrieved = await chat_crud.get_chat(db=test_db, chat_id=chat.id)
    assert retrieved is None


@pytest.mark.asyncio
async def test_add_message(test_db: AsyncSession):
    """Test adding a message to a chat"""
    # Create a chat
    chat = await chat_crud.create_chat(db=test_db, title="Test Chat")

    # Add a message
    message = await chat_crud.add_message(
        db=test_db,
        chat_id=chat.id,
        role="user",
        content="Hello, world!",
    )

    assert message.id is not None
    assert message.chat_id == chat.id
    assert message.role == "user"
    assert message.content == "Hello, world!"


@pytest.mark.asyncio
async def test_add_message_with_usage(test_db: AsyncSession):
    """Test adding a message with token usage"""
    chat = await chat_crud.create_chat(db=test_db)

    message = await chat_crud.add_message(
        db=test_db,
        chat_id=chat.id,
        role="assistant",
        content="Response",
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        finish_reason="stop",
    )

    assert message.prompt_tokens == 10
    assert message.completion_tokens == 20
    assert message.total_tokens == 30
    assert message.finish_reason == "stop"


@pytest.mark.asyncio
async def test_get_messages(test_db: AsyncSession):
    """Test getting messages for a chat"""
    chat = await chat_crud.create_chat(db=test_db)

    # Add multiple messages
    await chat_crud.add_message(db=test_db, chat_id=chat.id, role="user", content="Q1")
    await chat_crud.add_message(db=test_db, chat_id=chat.id, role="assistant", content="A1")
    await chat_crud.add_message(db=test_db, chat_id=chat.id, role="user", content="Q2")

    # Get messages
    messages = await chat_crud.get_messages(db=test_db, chat_id=chat.id)

    assert len(messages) == 3
    assert messages[0].role == "user"
    assert messages[0].content == "Q1"
    assert messages[1].role == "assistant"
    assert messages[2].role == "user"

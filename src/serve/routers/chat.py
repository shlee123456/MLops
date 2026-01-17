"""Chat completion endpoints"""

import logging
import time
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..cruds import chat as chat_crud
from ..schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCreate,
    ChatResponse,
    MessageResponse,
)
from .dependency import get_db_session, get_llm_client, verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["Chat"])


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completion(
    request: ChatCompletionRequest,
    authenticated: bool = Depends(verify_api_key),
    vllm_client=Depends(get_llm_client),
    db: AsyncSession = Depends(get_db_session),
):
    """Chat completion endpoint"""
    start_time = time.time()

    try:
        # Convert messages to dict format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Handle streaming mode
        if request.stream:
            async def generate():
                stream = vllm_client.chat_completion(
                    messages=messages,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    top_p=request.top_p,
                    stream=True
                )
                for chunk in stream:
                    yield f"data: {chunk}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")

        # Non-streaming mode
        response = vllm_client.chat_completion(
            messages=messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            stream=False
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        elapsed_time = time.time() - start_time

        # Log request
        logger.info(
            f"Chat completion - Model: {response['model']}, "
            f"Tokens: {response['usage'].get('total_tokens', 'N/A')}, "
            f"Time: {elapsed_time:.2f}s"
        )

        # Persist to database if session_id provided
        session_id = request.session_id
        if session_id:
            # Save user message
            user_msg = request.messages[-1]
            await chat_crud.add_message(
                db=db,
                chat_id=session_id,
                role=user_msg.role,
                content=user_msg.content,
            )
            # Save assistant response
            await chat_crud.add_message(
                db=db,
                chat_id=session_id,
                role="assistant",
                content=response["content"],
                prompt_tokens=response["usage"].get("prompt_tokens"),
                completion_tokens=response["usage"].get("completion_tokens"),
                total_tokens=response["usage"].get("total_tokens"),
                finish_reason=response.get("finish_reason"),
            )

        return ChatCompletionResponse(
            content=response["content"],
            model=response["model"],
            usage=response["usage"],
            finish_reason=response.get("finish_reason"),
            created_at=datetime.now().isoformat(),
            session_id=session_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Chat session management endpoints

@router.post("/chats", response_model=ChatResponse)
async def create_chat(
    request: ChatCreate,
    authenticated: bool = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new chat session"""
    chat = await chat_crud.create_chat(
        db=db,
        title=request.title,
        model=request.model,
    )
    return ChatResponse(
        id=chat.id,
        title=chat.title,
        model=chat.model,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        message_count=0,
    )


@router.get("/chats", response_model=List[ChatResponse])
async def list_chats(
    skip: int = 0,
    limit: int = 100,
    authenticated: bool = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
):
    """List all chat sessions"""
    chats = await chat_crud.get_chats(db=db, skip=skip, limit=limit)
    return [
        ChatResponse(
            id=chat.id,
            title=chat.title,
            model=chat.model,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            message_count=len(chat.messages) if hasattr(chat, 'messages') else 0,
        )
        for chat in chats
    ]


@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: str,
    authenticated: bool = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
):
    """Get a chat session by ID"""
    chat = await chat_crud.get_chat(db=db, chat_id=chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    return ChatResponse(
        id=chat.id,
        title=chat.title,
        model=chat.model,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        message_count=len(chat.messages) if chat.messages else 0,
    )


@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: str,
    authenticated: bool = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
):
    """Delete a chat session"""
    deleted = await chat_crud.delete_chat(db=db, chat_id=chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
    return {"message": "Chat deleted successfully"}


@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(
    chat_id: str,
    skip: int = 0,
    limit: int = 100,
    authenticated: bool = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db_session),
):
    """Get messages for a chat session"""
    # Verify chat exists
    chat = await chat_crud.get_chat(db=db, chat_id=chat_id, include_messages=False)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = await chat_crud.get_messages(db=db, chat_id=chat_id, skip=skip, limit=limit)
    return [MessageResponse.model_validate(msg) for msg in messages]

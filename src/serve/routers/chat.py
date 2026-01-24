"""
Chat Router

채팅 API 엔드포인트
"""

import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.serve.core.llm import LLMClient
from src.serve.core.metrics import record_llm_request
from src.serve.routers.dependency import get_db, get_llm_client, verify_api_key
from src.serve.schemas.chat import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    MessageResponse,
    LLMConfigCreate,
    LLMConfigUpdate,
    LLMConfigResponse,
    UsageResponse,
)
from src.serve.cruds import chat as crud

router = APIRouter(prefix="/v1", tags=["Chat"])


# ============================================================
# Chat Completion
# ============================================================

@router.post(
    "/chat/completions",
    response_model=ChatCompletionResponse,
    summary="채팅 완성",
    description="OpenAI 호환 채팅 완성 API",
)
async def chat_completion(
    request: ChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
    _: bool = Depends(verify_api_key),
):
    """채팅 완성 요청 처리"""
    start_time = time.time()
    
    # 메시지 변환
    messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
    
    # 스트리밍 모드
    if request.stream:
        async def generate():
            async for chunk in llm.chat_completion_stream(
                messages=messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
            ):
                yield f"data: {chunk}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(generate(), media_type="text/event-stream")
    
    # 일반 모드
    response = await llm.chat_completion(
        messages=messages,
        model=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        top_p=request.top_p,
    )
    
    if "error" in response:
        # 에러 메트릭 기록
        record_llm_request(
            model=request.model or "unknown",
            duration=time.time() - start_time,
            tokens=0,
            success=False
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response["error"],
        )
    
    latency_ms = int((time.time() - start_time) * 1000)
    conversation_id = request.conversation_id
    
    # 성공 메트릭 기록
    usage = response.get("usage", {})
    record_llm_request(
        model=response.get("model", request.model or "unknown"),
        duration=latency_ms / 1000.0,
        tokens=usage.get("total_tokens", 0),
        success=True
    )
    
    # 대화 저장
    if request.save_conversation:
        # 새 대화 또는 기존 대화에 추가
        if not conversation_id:
            conversation = await crud.create_conversation(db)
            conversation_id = conversation.id
        
        # 사용자 메시지 저장 (마지막 메시지가 user인 경우)
        if messages and messages[-1]["role"] == "user":
            await crud.create_message(
                db,
                conversation_id=conversation_id,
                role="user",
                content=messages[-1]["content"],
            )
        
        # 어시스턴트 응답 저장
        usage = response.get("usage", {})
        await crud.create_message(
            db,
            conversation_id=conversation_id,
            role="assistant",
            content=response["content"],
            model=response.get("model"),
            tokens_used=usage.get("total_tokens"),
            latency_ms=latency_ms,
        )
    
    return ChatCompletionResponse(
        content=response["content"],
        model=response.get("model", "unknown"),
        usage=UsageResponse(
            prompt_tokens=response.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=response.get("usage", {}).get("completion_tokens", 0),
            total_tokens=response.get("usage", {}).get("total_tokens", 0),
        ),
        finish_reason=response.get("finish_reason"),
        conversation_id=conversation_id,
        created_at=datetime.utcnow(),
    )


# ============================================================
# Conversations
# ============================================================

@router.post(
    "/conversations",
    response_model=ConversationListResponse,
    summary="대화 생성",
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    request: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """새 대화 세션 생성"""
    conversation = await crud.create_conversation(
        db,
        title=request.title,
        llm_config_id=request.llm_config_id,
        session_id=request.session_id,
    )
    return conversation


@router.get(
    "/conversations",
    response_model=list[ConversationListResponse],
    summary="대화 목록",
)
async def list_conversations(
    skip: int = 0,
    limit: int = 20,
    session_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """대화 목록 조회"""
    conversations = await crud.get_conversations(
        db, skip=skip, limit=limit, session_id=session_id
    )
    return conversations


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResponse,
    summary="대화 상세",
)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """대화 상세 조회 (메시지 포함)"""
    conversation = await crud.get_conversation(
        db, conversation_id, include_messages=True
    )
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conversation


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="대화 삭제",
)
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """대화 삭제"""
    deleted = await crud.delete_conversation(db, conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=list[MessageResponse],
    summary="메시지 목록",
)
async def get_messages(
    conversation_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """대화의 메시지 목록 조회"""
    messages = await crud.get_messages(db, conversation_id, skip=skip, limit=limit)
    return messages


# ============================================================
# LLM Configs
# ============================================================

@router.post(
    "/llm-configs",
    response_model=LLMConfigResponse,
    summary="LLM 설정 생성",
    status_code=status.HTTP_201_CREATED,
)
async def create_llm_config(
    request: LLMConfigCreate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """LLM 설정 프리셋 생성"""
    try:
        config = await crud.create_llm_config(
            db,
            name=request.name,
            model_name=request.model_name,
            system_prompt=request.system_prompt,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            is_default=request.is_default,
        )
        return config
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"LLM config with name '{request.name}' already exists",
        )


@router.get(
    "/llm-configs",
    response_model=list[LLMConfigResponse],
    summary="LLM 설정 목록",
)
async def list_llm_configs(
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """LLM 설정 목록 조회"""
    configs = await crud.get_llm_configs(db)
    return configs


@router.get(
    "/llm-configs/{config_id}",
    response_model=LLMConfigResponse,
    summary="LLM 설정 상세",
)
async def get_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """LLM 설정 상세 조회"""
    config = await crud.get_llm_config(db, config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM config not found",
        )
    return config


@router.put(
    "/llm-configs/{config_id}",
    response_model=LLMConfigResponse,
    summary="LLM 설정 수정",
)
async def update_llm_config(
    config_id: int,
    request: LLMConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """LLM 설정 부분 수정"""
    update_data = request.model_dump(exclude_unset=True)
    config = await crud.update_llm_config(db, config_id, **update_data)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM config not found",
        )
    return config


@router.delete(
    "/llm-configs/{config_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="LLM 설정 삭제",
)
async def delete_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_api_key),
):
    """LLM 설정 삭제 (참조 Conversation은 llm_config_id NULL 처리)"""
    deleted = await crud.delete_llm_config(db, config_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="LLM config not found",
        )

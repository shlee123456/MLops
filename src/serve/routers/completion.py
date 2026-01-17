"""Text completion endpoints"""

import logging
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from ..schemas.completion import CompletionRequest, CompletionResponse
from .dependency import get_llm_client, verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["Completion"])


@router.post("/completions", response_model=CompletionResponse)
async def completion(
    request: CompletionRequest,
    authenticated: bool = Depends(verify_api_key),
    vllm_client=Depends(get_llm_client),
):
    """Text completion endpoint"""
    start_time = time.time()

    try:
        response = vllm_client.completion(
            prompt=request.prompt,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        if "error" in response:
            raise HTTPException(status_code=500, detail=response["error"])

        elapsed_time = time.time() - start_time

        logger.info(
            f"Completion - Model: {response['model']}, "
            f"Tokens: {response['usage'].get('total_tokens', 'N/A')}, "
            f"Time: {elapsed_time:.2f}s"
        )

        return CompletionResponse(
            content=response["content"],
            model=response["model"],
            usage=response["usage"],
            created_at=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))

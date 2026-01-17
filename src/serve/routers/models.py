"""Model listing endpoints"""

from fastapi import APIRouter, Depends

from .dependency import verify_api_key, get_llm_client

router = APIRouter(prefix="/v1", tags=["Models"])


@router.get("/models")
async def list_models(
    authenticated: bool = Depends(verify_api_key),
    vllm_client=Depends(get_llm_client),
):
    """List available models"""
    models = vllm_client.list_models()
    return {
        "object": "list",
        "data": [{"id": model, "object": "model"} for model in models]
    }

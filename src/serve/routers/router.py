"""Combined API router"""

from fastapi import APIRouter

from .health import router as health_router
from .models import router as models_router
from .chat import router as chat_router
from .completion import router as completion_router

api_router = APIRouter()

# Include all routers
api_router.include_router(health_router)
api_router.include_router(models_router)
api_router.include_router(chat_router)
api_router.include_router(completion_router)

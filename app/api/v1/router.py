



from fastapi import APIRouter

from app.api.v1.endpoints import (
    health,
    chat,
    videos,
    sessions,
    auth,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(videos.router)
api_router.include_router(sessions.router)
api_router.include_router(auth.router)
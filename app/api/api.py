from fastapi import APIRouter

from app.api.endpoints import auth, notes, tags, collections, shares

api_router = APIRouter()

# Роутеры для различных эндпоинтов
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(tags.router, prefix="/tags", tags=["tags"])
api_router.include_router(collections.router, prefix="/collections", tags=["collections"])
api_router.include_router(shares.router, prefix="/notes", tags=["shares"]) 
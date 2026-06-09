from fastapi import APIRouter

from app.api.v1.endpoints import health, searches, weather, ai


api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(searches.router)
api_router.include_router(weather.router)
api_router.include_router(ai.router)
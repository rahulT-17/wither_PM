# backend/app/api/v1/endpoints/ai.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.llm import (
    WeatherInsightFromSearchResponse,
    WeatherInsightRequest,
    WeatherInsightResponse,
)
from app.services.llm_service import LLMService

router = APIRouter(prefix="/ai", tags=["ai"])


def get_llm_service(db: AsyncSession = Depends(get_db)) -> LLMService:
    return LLMService(db)


@router.post("/insight", response_model=WeatherInsightResponse)
async def insight(
    payload: WeatherInsightRequest,
    service: LLMService = Depends(get_llm_service),
) -> WeatherInsightResponse:
    return await service.generate_insight(payload)


@router.post("/insight/{search_id}", response_model=WeatherInsightFromSearchResponse)
async def insight_from_search(
    search_id: int,
    service: LLMService = Depends(get_llm_service),
) -> WeatherInsightFromSearchResponse:
    return await service.generate_insight_from_search(search_id)

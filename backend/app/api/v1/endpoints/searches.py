from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.weather_search import (
    WeatherSearchCreate,
    WeatherSearchRead,
    WeatherSearchUpdate,
)
from app.services.weather_search_service import WeatherSearchService

router = APIRouter(prefix="/searches", tags=["searches"])


@router.post("", response_model=WeatherSearchRead, status_code=status.HTTP_201_CREATED)
async def create_search(
    payload: WeatherSearchCreate,
    db: AsyncSession = Depends(get_db),
):
    service = WeatherSearchService(db)
    return await service.create(payload)


@router.get("", response_model=list[WeatherSearchRead])
async def list_searches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    service = WeatherSearchService(db)
    return await service.list(limit=limit, offset=offset)


@router.get("/{search_id}", response_model=WeatherSearchRead)
async def get_search(
    search_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = WeatherSearchService(db)
    return await service.get_by_id(search_id)


@router.put("/{search_id}", response_model=WeatherSearchRead)
async def update_search(
    search_id: int,
    payload: WeatherSearchUpdate,
    db: AsyncSession = Depends(get_db),
):
    service = WeatherSearchService(db)
    return await service.update(search_id, payload)


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_search(
    search_id: int,
    db: AsyncSession = Depends(get_db),
):
    service = WeatherSearchService(db)
    await service.delete(search_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
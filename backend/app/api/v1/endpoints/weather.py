from typing import Annotated, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from fastapi import APIRouter, Depends, Query

from app.schemas.weather import CurrentWeatherResponse, ForecastResponse, GeocodeItem
from app.schemas.weather_search import WeatherSearchCreate
from app.services.weather_service import WeatherService
from app.services.weather_search_service import WeatherSearchService

router = APIRouter(prefix="/weather", tags=["weather"])


def get_weather_service() -> WeatherService:
    return WeatherService()


@router.get("/geocode", response_model=list[GeocodeItem])
async def geocode(
    q: Annotated[str, Query(min_length=1, max_length=120)],
    limit: Annotated[int, Query(ge=1, le=10)] = 5,
    service: WeatherService = Depends(get_weather_service),
) -> list[GeocodeItem]:
    return await service.geocode(q=q, limit=limit)


@router.get("/current", response_model=CurrentWeatherResponse)
async def current_weather(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    units: Literal["metric", "imperial", "standard"] = "metric",
    service: WeatherService = Depends(get_weather_service),
) -> CurrentWeatherResponse:
    return await service.get_current_weather(lat=lat, lon=lon, units=units)


@router.get("/forecast", response_model=ForecastResponse)
async def forecast(
    lat: Annotated[float, Query(ge=-90, le=90)],
    lon: Annotated[float, Query(ge=-180, le=180)],
    units: Literal["metric", "imperial", "standard"] = "metric",
    service: WeatherService = Depends(get_weather_service),
) -> ForecastResponse:
    return await service.get_forecast(lat=lat, lon=lon, units=units)


@router.get("/search")
async def search(
    q: Annotated[str, Query(min_length=1, max_length=120)],
    units: Literal["metric", "imperial", "standard"] = "metric",
    service: WeatherService = Depends(get_weather_service),
    db: AsyncSession = Depends(get_db),
):
    result = await service.search_by_city(query=q, units=units)

    summary = service.build_summary(
        query=q,
        location=result["location"],
        current=result["current"],
        forecast=result["forecast"],
        units=units,
    )

    await WeatherSearchService(db).upsert(
        WeatherSearchCreate(
            location=q,
            resolved_city=result["location"].name,
            country_code=result["location"].country,
            latitude=result["location"].lat,
            longitude=result["location"].lon,
            units=units,
            weather_data=summary,
        )
    )

    return result
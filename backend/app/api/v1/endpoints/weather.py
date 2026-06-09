from typing import Annotated, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.schemas.weather_search import WeatherSearchCreate
from app.schemas.parser import ParseWeatherQueryRequest
from app.services.parser_service import ParserService
from app.services.weather_service import WeatherService
from app.services.weather_search_service import WeatherSearchService

router = APIRouter(prefix="/weather", tags=["weather"])


def get_weather_service() -> WeatherService:
    return WeatherService()


def get_parser_service() -> ParserService:
    return ParserService()


@router.get("/search")
async def search(
    q: Annotated[str, Query(min_length=1, max_length=120)],
    units: Literal["metric", "imperial", "standard"] = "metric",
    service: WeatherService = Depends(get_weather_service),
    parser: ParserService = Depends(get_parser_service),
    db: AsyncSession = Depends(get_db),
):
    try:
        parsed = parser.parse(ParseWeatherQueryRequest(text=q))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    result = await service.search_by_city(query=parsed.location, units=parsed.units or units)

    summary = service.build_summary(
        query=q,
        location=result["location"],
        current=result["current"],
        forecast=result["forecast"],
        units=parsed.units or units,
    )

    persisted_snapshot = {
        "query": q,
        "units": parsed.units or units,
        "resolved_city": result["location"].name,
        "country_code": result["location"].country,
        "lat": result["location"].lat,
        "lon": result["location"].lon,
        "start_date": parsed.start_date.isoformat() if parsed.start_date else None,
        "end_date": parsed.end_date.isoformat() if parsed.end_date else None,
        "summary": summary,
        "current": result["current"].model_dump(mode="json"),
        "forecast": result["forecast"].model_dump(mode="json"),
    }

    saved = await WeatherSearchService(db).upsert(
        WeatherSearchCreate(
            location=q,
            resolved_city=result["location"].name,
            country_code=result["location"].country,
            latitude=result["location"].lat,
            longitude=result["location"].lon,
            start_date=parsed.start_date,
            end_date=parsed.end_date,
            units=parsed.units or units,
            weather_data=persisted_snapshot,
        )
    )

    return {
        "query": q,
        "parsed": parsed,
        "location": result["location"],
        "current": result["current"],
        "forecast": result["forecast"],
        "saved_search_id": saved.id,
        "saved_search_key": saved.search_key,
    }

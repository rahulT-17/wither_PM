from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UpstreamServiceError
from app.schemas.llm import (
    WeatherInsightFromSearchResponse,
    WeatherInsightRequest,
    WeatherInsightResponse,
)
from app.services.groq_client import GroqClient
from app.services.weather_search_service import WeatherSearchService


class LLMService:
    def __init__(self, db: AsyncSession | None = None) -> None:
        self.client = GroqClient()
        self.search_service = WeatherSearchService(db) if db is not None else None

    async def generate_insight(self, payload: WeatherInsightRequest) -> WeatherInsightResponse:
        return await self.client.generate_insight(
            query=payload.query,
            location=payload.location,
            units=payload.units,
            current=payload.current.model_dump(mode="json"),
            forecast=payload.forecast.model_dump(mode="json"),
        )

    async def generate_insight_from_search(self, search_id: int) -> WeatherInsightFromSearchResponse:
        if self.search_service is None:
            raise UpstreamServiceError("Database session is required for persisted insight generation")

        search = await self.search_service.get_by_id(search_id)

        if not search.weather_data:
            raise UpstreamServiceError("Persisted search does not contain weather_data")

        weather_data = search.weather_data
        current = weather_data.get("current")
        forecast = weather_data.get("forecast")

        if not current or not forecast:
            raise UpstreamServiceError("Persisted search is missing current or forecast weather data")

        insight = await self.client.generate_insight(
            query=weather_data.get("query") or search.location,
            location=weather_data.get("resolved_city") or search.resolved_city or search.location,
            units=weather_data.get("units") or search.units.value,
            current=current,
            forecast=forecast,
        )

        return WeatherInsightFromSearchResponse(
            search_id=search.id,
            search_key=search.search_key,
            location=weather_data.get("resolved_city") or search.location,
            insight=insight,
        )

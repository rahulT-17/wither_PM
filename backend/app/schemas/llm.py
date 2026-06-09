from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.weather import CurrentWeatherResponse, ForecastResponse


class WeatherInsightRequest(BaseModel):
    query: str = Field(min_length=1, max_length=300)
    location: str = Field(min_length=1, max_length=255)
    units: Literal["metric", "imperial", "standard"] = "metric"
    current: CurrentWeatherResponse
    forecast: ForecastResponse

    model_config = ConfigDict(extra="forbid")


class WeatherInsightResponse(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=500)
    recommendations: list[str] = Field(min_length=1, max_length=5)
    packing_tips: list[str] = Field(default_factory=list, max_length=5)
    risk_level: Literal["low", "medium", "high"]
    outdoor_score: int = Field(ge=0, le=100)

    model_config = ConfigDict(extra="forbid")


class WeatherInsightFromSearchResponse(BaseModel):
    search_id: int
    search_key: str
    location: str
    insight: WeatherInsightResponse

    model_config = ConfigDict(extra="forbid")

from datetime import date, datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from pydantic import BaseModel, Field

from app.models.weather_search import Units


class WeatherSearchBase(BaseModel):
    location: str = Field(min_length=1, max_length=255)
    resolved_city: str | None = Field(default=None, max_length=255)
    country_code: str | None = Field(default=None, max_length=8)
    latitude: float | None = None
    longitude: float | None = None
    start_date: date | None = None
    end_date: date | None = None
    units: Units = Units.metric
    notes: str | None = None
    weather_data: dict | None = None


class WeatherSearchCreate(WeatherSearchBase):
    pass


class WeatherSearchUpdate(BaseModel):
    location: str | None = Field(default=None, min_length=1, max_length=255)
    resolved_city: str | None = Field(default=None, max_length=255)
    country_code: str | None = Field(default=None, max_length=8)
    latitude: float | None = None
    longitude: float | None = None
    start_date: date | None = None
    end_date: date | None = None
    units: Units | None = None
    notes: str | None = None
    weather_data: dict | None = None


class WeatherSearchRead(WeatherSearchBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ParseWeatherQueryRequest(BaseModel):
    text: str = Field(min_length=1, max_length=300)
    reference_date: date | None = None


class ParseWeatherQueryResponse(BaseModel):
    location: str = Field(min_length=1, max_length=255)
    units: Literal["metric", "imperial", "standard"] = "metric"
    start_date: date | None = None
    end_date: date | None = None
    intent: Literal["current", "forecast", "both"] = "both"
    confidence: float = Field(ge=0.0, le=1.0)
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")
from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SqlEnum, Float, Index, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Units(str, Enum):
    metric = "metric"
    imperial = "imperial"
    standard = "standard"


class WeatherSearch(Base):
    __tablename__ = "weather_searches"
    __table_args__ = (
        Index("ix_weather_searches_location", "location"),
        Index("ix_weather_searches_created_at", "created_at"),
        UniqueConstraint("search_key", name="uq_weather_searches_search_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    search_key: Mapped[str] = mapped_column(String(64), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    resolved_city: Mapped[str | None] = mapped_column(String(255))
    country_code: Mapped[str | None] = mapped_column(String(8))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    units: Mapped[Units] = mapped_column(SqlEnum(Units), default=Units.metric, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    weather_data: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

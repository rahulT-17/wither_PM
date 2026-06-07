from hashlib import sha256

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.weather_search_repository import WeatherSearchRepository
from app.schemas.weather_search import WeatherSearchCreate, WeatherSearchUpdate


class WeatherSearchService:
    def __init__(self, db: AsyncSession) -> None:
        self.repo = WeatherSearchRepository(db)

    @staticmethod
    def _validate_date_range(start_date, end_date) -> None:
        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="start_date cannot be after end_date",
            )

    @staticmethod
    def _normalize(value: str | None) -> str:
        return " ".join((value or "").strip().lower().split())

    @classmethod
    def build_search_key(cls, payload: WeatherSearchCreate) -> str:
        parts = [
            cls._normalize(payload.location),
            cls._normalize(payload.resolved_city),
            (payload.country_code or "").strip().upper(),
            payload.units.value if hasattr(payload.units, "value") else str(payload.units),
            payload.start_date.isoformat() if payload.start_date else "",
            payload.end_date.isoformat() if payload.end_date else "",
        ]
        digest = sha256("|".join(parts).encode("utf-8")).hexdigest()
        return digest

    @classmethod
    def with_search_key(cls, payload: WeatherSearchCreate) -> WeatherSearchCreate:
        data = payload.model_dump()
        data["search_key"] = cls.build_search_key(payload)
        return WeatherSearchCreate(**data)

    async def create(self, payload: WeatherSearchCreate):
        payload = self.with_search_key(payload)
        if not payload.location.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="location cannot be empty",
            )
        self._validate_date_range(payload.start_date, payload.end_date)
        return await self.repo.create(payload)

    async def get_by_id(self, search_id: int):
        obj = await self.repo.get_by_id(search_id)
        if not obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Search id={search_id} not found",
            )
        return obj

    async def list(self, limit: int, offset: int):
        return await self.repo.list(limit=limit, offset=offset)

    async def update(self, search_id: int, payload: WeatherSearchUpdate):
        obj = await self.get_by_id(search_id)

        next_start = payload.start_date if payload.start_date is not None else obj.start_date
        next_end = payload.end_date if payload.end_date is not None else obj.end_date
        self._validate_date_range(next_start, next_end)

        if payload.location is not None and not payload.location.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="location cannot be empty",
            )

        return await self.repo.update(obj, payload)

    async def upsert(self, payload: WeatherSearchCreate):
        payload = self.with_search_key(payload)
        if not payload.location.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="location cannot be empty",
            )
        self._validate_date_range(payload.start_date, payload.end_date)
        return await self.repo.upsert(payload)

    async def delete(self, search_id: int) -> None:
        obj = await self.get_by_id(search_id)
        await self.repo.delete(obj)
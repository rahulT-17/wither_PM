from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.weather_search import WeatherSearch
from app.schemas.weather_search import WeatherSearchCreate, WeatherSearchUpdate


class WeatherSearchRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, payload: WeatherSearchCreate) -> WeatherSearch:
        obj = WeatherSearch(**payload.model_dump())
        self.db.add(obj)
        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def get_by_id(self, search_id: int) -> WeatherSearch | None:
        result = await self.db.execute(
            select(WeatherSearch).where(WeatherSearch.id == search_id)
        )
        return result.scalar_one_or_none()

    async def list(self, limit: int = 20, offset: int = 0) -> list[WeatherSearch]:
        result = await self.db.execute(
            select(WeatherSearch)
            .order_by(WeatherSearch.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update(self, obj: WeatherSearch, payload: WeatherSearchUpdate) -> WeatherSearch:
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(obj, field, value)

        await self.db.commit()
        await self.db.refresh(obj)
        return obj

    async def delete(self, obj: WeatherSearch) -> None:
        await self.db.delete(obj)
        await self.db.commit()
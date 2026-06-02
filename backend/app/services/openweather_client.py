from typing import Any

import httpx
from fastapi import HTTPException, status

from app.core.config import get_settings

settings = get_settings()


class OpenWeatherClient:
    def __init__(self) -> None:
        self.base_url = settings.OPENWEATHER_BASE_URL.rstrip("/")
        self.api_key = settings.OPENWEATHER_API_KEY
        self.timeout = settings.OPENWEATHER_TIMEOUT_SECONDS

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="OPENWEATHER_API_KEY is not configured",
            )

        query = {**params, "appid": self.api_key}
        url = f"{self.base_url}{path}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(url, params=query)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="OpenWeather timed out")
        except httpx.HTTPError:
            raise HTTPException(status_code=502, detail="OpenWeather request failed")

        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Location not found")
        if resp.status_code >= 400:
            raise HTTPException(status_code=502, detail="OpenWeather upstream error")

        return resp.json()

    async def geocode(self, q: str, limit: int = 5) -> list[dict[str, Any]]:
        data = await self._get("/geo/1.0/direct", {"q": q, "limit": limit})
        if not isinstance(data, list):
            raise HTTPException(status_code=502, detail="Invalid geocode response")
        return data

    async def current_weather(self, lat: float, lon: float, units: str = "metric") -> dict[str, Any]:
        return await self._get("/data/2.5/weather", {"lat": lat, "lon": lon, "units": units})

    async def forecast(self, lat: float, lon: float, units: str = "metric") -> dict[str, Any]:
        return await self._get("/data/2.5/forecast", {"lat": lat, "lon": lon, "units": units})
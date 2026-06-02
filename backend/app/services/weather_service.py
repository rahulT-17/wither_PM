from fastapi import HTTPException, status

from app.schemas.weather import CurrentWeatherResponse, ForecastResponse, GeocodeItem
from app.schemas.weather_search import WeatherSearchCreate
from app.services.openweather_client import OpenWeatherClient


class WeatherService:
    def __init__(self) -> None:
        self.client = OpenWeatherClient()

    async def geocode(self, q: str, limit: int = 5) -> list[GeocodeItem]:
        if not q.strip():
            raise HTTPException(status_code=422, detail="q cannot be empty")
        raw = await self.client.geocode(q=q.strip(), limit=limit)
        return [GeocodeItem(**item) for item in raw]

    async def get_current_weather(self, lat: float, lon: float, units: str) -> CurrentWeatherResponse:
        raw = await self.client.current_weather(lat=lat, lon=lon, units=units)
        try:
            return CurrentWeatherResponse(
                city=raw["name"],
                country=raw.get("sys", {}).get("country"),
                lat=raw["coord"]["lat"],
                lon=raw["coord"]["lon"],
                main={
                    "temp": raw["main"]["temp"],
                    "feels_like": raw["main"]["feels_like"],
                    "humidity": raw["main"]["humidity"],
                    "pressure": raw["main"]["pressure"],
                },
                weather=[
                    {
                        "main": item["main"],
                        "description": item["description"],
                        "icon": item["icon"],
                    }
                    for item in raw.get("weather", [])
                ],
                wind_speed=raw.get("wind", {}).get("speed"),
                timestamp=raw["dt"],
            )
        except KeyError as exc:
            raise HTTPException(status_code=502, detail="Malformed current weather response") from exc

    async def get_forecast(self, lat: float, lon: float, units: str) -> ForecastResponse:
        raw = await self.client.forecast(lat=lat, lon=lon, units=units)
        try:
            items = [
                {
                    "timestamp": item["dt"],
                    "temp": item["main"]["temp"],
                    "feels_like": item["main"]["feels_like"],
                    "humidity": item["main"]["humidity"],
                    "weather_main": item["weather"][0]["main"],
                    "weather_description": item["weather"][0]["description"],
                    "icon": item["weather"][0]["icon"],
                    "wind_speed": item.get("wind", {}).get("speed"),
                }
                for item in raw.get("list", [])
            ]
            city = raw["city"]
            return ForecastResponse(
                city=city["name"],
                country=city.get("country"),
                lat=city["coord"]["lat"],
                lon=city["coord"]["lon"],
                items=items,
            )
        except (KeyError, IndexError) as exc:
            raise HTTPException(status_code=502, detail="Malformed forecast response") from exc

    async def search_by_city(self, query: str, units: str = "metric") -> dict:
        matches = await self.geocode(q=query, limit=5)
        if not matches:
            raise HTTPException(status_code=404, detail="Location not found")

        location = matches[0]
        current = await self.get_current_weather(lat=location.lat, lon=location.lon, units=units)
        forecast = await self.get_forecast(lat=location.lat, lon=location.lon, units=units)

        return {
            "query": query,
            "location": location,
            "current": current,
            "forecast": forecast,
        }
    
    def build_summary(self, query: str, location: GeocodeItem, current: CurrentWeatherResponse,
                      forecast: ForecastResponse, units: str) -> dict:
        return {
            "query": query,
            "units": units,
            "resolved_city": location.name,
            "country_code": location.country,
            "lat": location.lat,
            "lon": location.lon,
            "current": {
                "temp": current.main.temp,
                "feels_like": current.main.feels_like,
                "humidity": current.main.humidity,
                "condition": current.weather[0].main if current.weather else None,
            },
            "forecast_count": len(forecast.items),
        }
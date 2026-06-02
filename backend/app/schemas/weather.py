from pydantic import BaseModel, Field



class GeocodeItem(BaseModel):
    name: str
    lat: float
    lon: float
    country: str | None = None
    state: str | None = None


class WeatherMain(BaseModel):
    temp: float
    feels_like: float
    humidity: int
    pressure: int


class WeatherCondition(BaseModel):
    main: str
    description: str
    icon: str


class CurrentWeatherResponse(BaseModel):
    city: str
    country: str | None = None
    lat: float
    lon: float
    main: WeatherMain
    weather: list[WeatherCondition]
    wind_speed: float | None = None
    timestamp: int


class ForecastItem(BaseModel):
    timestamp: int
    temp: float
    feels_like: float
    humidity: int
    weather_main: str
    weather_description: str
    icon: str
    wind_speed: float | None = None


class ForecastResponse(BaseModel):
    city: str
    country: str | None = None
    lat: float
    lon: float
    items: list[ForecastItem]

class WeatherSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=120)
    units: str = Field(default="metric")


class WeatherSearchResponse(BaseModel):
    query: str
    location: GeocodeItem
    current: CurrentWeatherResponse
    forecast: ForecastResponse
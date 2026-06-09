import json
import logging
from datetime import datetime, timezone
from typing import Any, Literal

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    PermissionDeniedError,
    RateLimitError,
    UnprocessableEntityError,
)

from app.core.config import get_settings
from app.core.exceptions import (
    ConfigurationError,
    UpstreamRateLimitError,
    UpstreamServiceError,
    UpstreamTimeoutError,
)
from app.schemas.llm import WeatherInsightResponse

logger = logging.getLogger(__name__)
settings = get_settings()


class GroqClient:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            timeout=settings.GROQ_TIMEOUT_SECONDS,
        )
        self.model = settings.GROQ_INSIGHT_MODEL
        self.max_completion_tokens = settings.GROQ_MAX_COMPLETION_TOKENS

    @staticmethod
    def _compact_current(current: dict[str, Any]) -> dict[str, Any]:
        main = current.get("main") or {}
        weather = current.get("weather") or []
        weather_item = weather[0] if weather and isinstance(weather, list) else {}
        return {
            "city": current.get("city"),
            "country": current.get("country"),
            "lat": current.get("lat"),
            "lon": current.get("lon"),
            "temperature": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "humidity": main.get("humidity"),
            "pressure": main.get("pressure"),
            "condition": weather_item.get("main"),
            "description": weather_item.get("description"),
            "wind_speed": current.get("wind_speed"),
            "timestamp": current.get("timestamp"),
        }

    @staticmethod
    def _compact_forecast(forecast: dict[str, Any]) -> dict[str, Any]:
        raw_items = forecast.get("items") or []
        compact_items: list[dict[str, Any]] = []

        if isinstance(raw_items, list):
            sampled_items = raw_items[::8] or raw_items[:5]
            for item in sampled_items[:5]:
                if not isinstance(item, dict):
                    continue

                timestamp = item.get("timestamp")
                forecast_day = None
                if isinstance(timestamp, int):
                    forecast_day = datetime.fromtimestamp(timestamp, tz=timezone.utc).date().isoformat()

                compact_items.append(
                    {
                        "day": forecast_day,
                        "timestamp": timestamp,
                        "temp": item.get("temp"),
                        "feels_like": item.get("feels_like"),
                        "humidity": item.get("humidity"),
                        "weather_main": item.get("weather_main"),
                        "weather_description": item.get("weather_description"),
                        "icon": item.get("icon"),
                        "wind_speed": item.get("wind_speed"),
                    }
                )

        return {
            "city": forecast.get("city"),
            "country": forecast.get("country"),
            "lat": forecast.get("lat"),
            "lon": forecast.get("lon"),
            "window_days": min(5, len(compact_items)) if compact_items else 0,
            "items": compact_items,
        }

    @classmethod
    def _compact_payload(
        cls,
        *,
        query: str,
        location: str,
        units: Literal["metric", "imperial", "standard"],
        current: dict[str, Any],
        forecast: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "query": query,
            "location": location,
            "units": units,
            "current": cls._compact_current(current),
            "forecast": cls._compact_forecast(forecast),
        }

    @staticmethod
    def _response_text(exc: Exception) -> str | None:
        response = getattr(exc, "response", None)
        if response is None:
            return None

        text = getattr(response, "text", None)
        if text:
            return text

        content = getattr(response, "content", None)
        if isinstance(content, bytes):
            try:
                return content.decode("utf-8", errors="ignore")
            except Exception:
                return None
        if isinstance(content, str):
            return content
        return None

    async def generate_insight(
        self,
        *,
        query: str,
        location: str,
        units: Literal["metric", "imperial", "standard"],
        current: dict[str, Any],
        forecast: dict[str, Any],
    ) -> WeatherInsightResponse:
        if not settings.GROQ_API_KEY:
            raise ConfigurationError("GROQ_API_KEY is not configured")

        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": 5,
                },
                "packing_tips": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 0,
                    "maxItems": 5,
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                },
                "outdoor_score": {"type": "integer", "minimum": 0, "maximum": 100},
            },
            "required": [
                "title",
                "summary",
                "recommendations",
                "packing_tips",
                "risk_level",
                "outdoor_score",
            ],
        }

        payload = self._compact_payload(
            query=query,
            location=location,
            units=units,
            current=current,
            forecast=forecast,
        )

        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a practical weather assistant. "
                            "Use only the provided weather data. "
                            "Return concise, user-friendly recommendations."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(payload),
                    },
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "weather_insight",
                        "strict": True,
                        "schema": schema,
                    },
                },
                temperature=0.4,
                max_completion_tokens=self.max_completion_tokens,
            )
        except APITimeoutError as exc:
            logger.warning(
                "Groq timeout",
                extra={"location": location, "units": units, "query": query},
            )
            raise UpstreamTimeoutError("Groq request timed out") from exc
        except APIConnectionError as exc:
            logger.warning(
                "Groq connection failure",
                extra={"location": location, "units": units, "query": query},
            )
            raise UpstreamServiceError("Groq network request failed") from exc
        except RateLimitError as exc:
            logger.warning(
                "Groq rate limited",
                extra={"location": location, "units": units, "query": query},
            )
            raise UpstreamRateLimitError("Groq rate limit hit") from exc
        except (AuthenticationError, PermissionDeniedError) as exc:
            logger.exception("Groq authentication failure")
            raise ConfigurationError("Groq authentication failed") from exc
        except (BadRequestError, UnprocessableEntityError) as exc:
            response_text = self._response_text(exc)
            logger.exception(
                "Groq rejected the request payload",
                extra={
                    "location": location,
                    "units": units,
                    "query": query,
                    "response_body": (response_text[:1000] if response_text else None),
                },
            )
            raise UpstreamServiceError(
                "Groq rejected the request payload",
                details={
                    "status_code": getattr(exc, "status_code", None),
                    "response_body": response_text[:1000] if response_text else None,
                },
            ) from exc
        except APIStatusError as exc:
            response_text = self._response_text(exc)
            logger.exception(
                "Groq API status error",
                extra={
                    "status_code": exc.status_code,
                    "request_id": getattr(exc, "request_id", None),
                    "location": location,
                    "units": units,
                    "query": query,
                    "response_body": (response_text[:1000] if response_text else None),
                },
            )
            raise UpstreamServiceError(
                "Groq returned an unexpected status",
                details={
                    "status_code": exc.status_code,
                    "request_id": getattr(exc, "request_id", None),
                    "response_body": response_text[:1000] if response_text else None,
                },
            ) from exc
        except Exception as exc:
            logger.exception(
                "Unexpected Groq failure",
                extra={"location": location, "units": units, "query": query},
            )
            raise UpstreamServiceError("Groq request failed") from exc

        content = resp.choices[0].message.content
        if not content:
            raise UpstreamServiceError("Groq returned empty content")

        try:
            return WeatherInsightResponse.model_validate_json(content)
        except Exception as exc:
            logger.exception("Groq returned invalid JSON")
            raise UpstreamServiceError("Groq returned invalid JSON") from exc

import re
from datetime import date, timedelta

from app.schemas.parser import ParseWeatherQueryRequest, ParseWeatherQueryResponse


class ParserService:
    _CITY_PATTERNS = [
        re.compile(r"\bweather in (?P<location>.+?)(?:\s+next\s+weekend|\s+this\s+weekend|\s+tomorrow|\s+today|$)", re.IGNORECASE),
        re.compile(r"\bin (?P<location>.+?)(?:\s+next\s+weekend|\s+this\s+weekend|\s+tomorrow|\s+today|$)", re.IGNORECASE),
        re.compile(r"^(?P<location>[A-Za-z\s,.-]{2,})$", re.IGNORECASE),
    ]

    @staticmethod
    def _normalize_location(value: str) -> str:
        return " ".join(value.strip().split())

    @staticmethod
    def _weekend_window(reference: date) -> tuple[date, date]:
        days_until_saturday = (5 - reference.weekday()) % 7
        saturday = reference + timedelta(days=days_until_saturday)
        sunday = saturday + timedelta(days=1)
        return saturday, sunday

    @staticmethod
    def _next_weekend_window(reference: date) -> tuple[date, date]:
        days_until_saturday = (5 - reference.weekday()) % 7
        if days_until_saturday == 0:
            days_until_saturday = 7
        saturday = reference + timedelta(days=days_until_saturday)
        sunday = saturday + timedelta(days=1)
        return saturday, sunday

    def parse(self, payload: ParseWeatherQueryRequest) -> ParseWeatherQueryResponse:
        text = payload.text.strip()
        reference = payload.reference_date or date.today()
        lower = text.lower()

        units = "metric"
        if any(word in lower for word in ["fahrenheit", "f"]):
            units = "imperial"
        elif any(word in lower for word in ["celsius", "c"]):
            units = "metric"

        start_date = None
        end_date = None
        intent = "both"
        notes = None

        if "today" in lower:
            start_date = reference
            end_date = reference
            intent = "current"
        elif "tomorrow" in lower:
            start_date = reference + timedelta(days=1)
            end_date = start_date
            intent = "forecast"
        elif "this weekend" in lower:
            start_date, end_date = self._weekend_window(reference)
            intent = "forecast"
        elif "next weekend" in lower:
            start_date, end_date = self._next_weekend_window(reference)
            intent = "forecast"

        location = None
        for pattern in self._CITY_PATTERNS:
            match = pattern.search(text)
            if match:
                location = self._normalize_location(match.group("location"))
                break

        if not location:
            raise ValueError("Could not extract a location from the query")

        confidence = 0.95
        if "weather" not in lower:
            confidence -= 0.2

        return ParseWeatherQueryResponse(
            location=location,
            units=units, 
            start_date=start_date,
            end_date=end_date,
            intent=intent,
            confidence=max(0.0, confidence),
            notes=notes,
        )
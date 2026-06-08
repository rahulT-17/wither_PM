class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(AppError):
    status_code = 500
    code = "configuration_error"


class ValidationAppError(AppError):
    status_code = 422
    code = "validation_error"


class UpstreamServiceError(AppError):
    status_code = 502
    code = "upstream_service_error"


class UpstreamTimeoutError(AppError):
    status_code = 504
    code = "upstream_timeout"


class UpstreamRateLimitError(AppError):
    status_code = 429
    code = "upstream_rate_limited"

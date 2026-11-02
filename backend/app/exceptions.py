class AppError(Exception):
    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str = "Внутренняя ошибка приложения") -> None:
        super().__init__(message)
        self.message = message


class BadRequestError(AppError):
    status_code: int = 400
    code: str = "bad_request"


class InvalidApiKeyError(AppError):
    status_code: int = 401
    code: str = "invalid_api_key"


class GenerationNotAvailableError(AppError):
    status_code: int = 501
    code: str = "generation_not_available"


class RateLimitError(AppError):
    status_code: int = 429
    code: str = "rate_limited"


class UpstreamTimeoutError(AppError):
    status_code: int = 504
    code: str = "upstream_timeout"


class ServiceUnavailableError(AppError):
    status_code: int = 503
    code: str = "provider_unavailable"


class InvalidModelResponseError(AppError):
    status_code: int = 422
    code: str = "invalid_model_response"

    def __init__(self, message: str = "Модель вернула некорректный результат") -> None:
        super().__init__(message)

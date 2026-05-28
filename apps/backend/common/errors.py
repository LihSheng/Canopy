class AppError(Exception):
    message: str
    status_code: int

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class AuthError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found"):
        super().__init__(message, status_code=404)


class SyncError(AppError):
    def __init__(self, message: str):
        super().__init__(message, status_code=502)


class IngestionTransformNotAllowedError(AppError):
    def __init__(self, blocked_keys: list[str]):
        super().__init__(
            "Transformation settings are not allowed at landing stage",
            status_code=422,
        )
        self.code = "INGESTION_TRANSFORM_NOT_ALLOWED"
        self.blocked_keys = blocked_keys

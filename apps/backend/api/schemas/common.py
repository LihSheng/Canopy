from pydantic import BaseModel

T = None


class ApiResponse[T](BaseModel):
    success: bool
    data: T | None = None
    error: str | None = None
    meta: dict | None = None


class ErrorDetail(BaseModel):
    detail: str


class ValidationErrorDetail(BaseModel):
    detail: list[dict]

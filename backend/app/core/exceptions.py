from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Any, Optional, Dict


class FoodBookException(Exception):
    """Base exception for all FoodBook domain errors."""
    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[Any] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class NotFoundException(FoodBookException):
    def __init__(self, message: str = "Resource not found", error_code: str = "NOT_FOUND", details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
        )


class UnauthorizedException(FoodBookException):
    def __init__(self, message: str = "Authentication required", error_code: str = "UNAUTHORIZED", details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class ForbiddenException(FoodBookException):
    def __init__(self, message: str = "Permission denied", error_code: str = "FORBIDDEN", details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
        )


class BadRequestException(FoodBookException):
    def __init__(self, message: str = "Bad request", error_code: str = "BAD_REQUEST", details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class ConflictException(FoodBookException):
    def __init__(self, message: str = "Resource conflict", error_code: str = "CONFLICT", details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_409_CONFLICT,
            details=details
        )


class DatabaseException(FoodBookException):
    def __init__(self, message: str = "Database operation failed", error_code: str = "DATABASE_ERROR", details: Optional[Any] = None):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


async def foodbook_exception_handler(request: Request, exc: FoodBookException) -> JSONResponse:
    content: Dict[str, Any] = {
        "success": False,
        "message": exc.message,
        "error_code": exc.error_code,
    }
    if exc.details:
        content["details"] = exc.details
    return JSONResponse(status_code=exc.status_code, content=content)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = []
    for err in exc.errors():
        field = ".".join([str(loc) for loc in err["loc"] if loc != "body"])
        errors.append({
            "field": field,
            "message": err["msg"],
            "type": err["type"]
        })
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "message": "Validation error in request data",
            "error_code": "VALIDATION_ERROR",
            "details": errors
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": exc.detail if isinstance(exc.detail, str) else "HTTP Exception",
            "error_code": f"HTTP_{exc.status_code}",
            "details": exc.detail if not isinstance(exc.detail, str) else None
        }
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected internal server error occurred",
            "error_code": "INTERNAL_SERVER_ERROR",
            "details": str(exc) if settings_debug_enabled() else None
        }
    )


def settings_debug_enabled() -> bool:
    from app.core.config import settings
    return settings.DEBUG

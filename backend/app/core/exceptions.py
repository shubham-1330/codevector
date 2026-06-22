import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("codevector.exceptions")


class AppError(Exception):
    """Base application error with an HTTP status code."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidCursorError(AppError):
    def __init__(self, detail: str = "Cursor is invalid or has expired") -> None:
        super().__init__(detail, status_code=400)


class InvalidParameterError(AppError):
    def __init__(self, detail: str) -> None:
        super().__init__(detail, status_code=422)


class NotFoundError(AppError):
    def __init__(self, detail: str = "Resource not found") -> None:
        super().__init__(detail, status_code=404)


class DatabaseError(AppError):
    def __init__(self, detail: str = "A database error occurred") -> None:
        super().__init__(detail, status_code=503)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(
        "Application error on %s %s: [%d] %s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message, "status_code": exc.status_code},
    )


async def unhandled_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={"error": "An unexpected error occurred", "status_code": 500},
    )

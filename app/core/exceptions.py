from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.logger import logger


class AppException(Exception):
    """Base class for custom application exceptions"""

    def __init__(self, message: str, status_code: int = 400, detail: str = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail


async def app_exception_handler(request: Request, exc: AppException):
    """Global handler for AppException to return consistent JSON responses"""
    logger.error(
        f"AppException: {exc.message} | Detail: {exc.detail} | Path: {request.url.path}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.message, "detail": exc.detail},
    )

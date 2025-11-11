from fastapi import Request
from fastapi.responses import JSONResponse
from .logging import get_logger

logger = get_logger(__name__)

async def exception_handler(request: Request, exc: Exception):
    logger.error(f"An error occurred: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "An internal server error occurred."},
    )

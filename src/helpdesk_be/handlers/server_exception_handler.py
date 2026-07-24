from fastapi import status
from fastapi.requests import Request
from fastapi.responses import JSONResponse


def handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "システムエラーが発生しました"},
    )

from fastapi import status
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from helpdesk_be.schemas.response.v1.error import ErrorResponse


def handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(detail="システムエラーが発生しました", type="INTERNAL_SERVER_ERROR").model_dump(),
    )


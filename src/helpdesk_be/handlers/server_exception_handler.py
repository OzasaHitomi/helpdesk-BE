from fastapi import status
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from helpdesk_be.core.config.base import core_settings
from helpdesk_be.schemas.response.v1.error import ErrorResponse


def handler(request: Request, exc: Exception) -> JSONResponse:
    response = JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            detail="システムエラーが発生しました", type="INTERNAL_SERVER_ERROR"
        ).model_dump(),
    )
    response.headers["Access-Control-Allow-Origin"] = core_settings.front_end_url
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"

    return response

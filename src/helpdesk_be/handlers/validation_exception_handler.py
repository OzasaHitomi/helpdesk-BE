from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from helpdesk_be.schemas.response.v1.error import ErrorResponse, ValidationErrorResponseItem


def handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    # detail = [{loc: ["body", "title"], type:"missing"}, {loc: [], type:""}, ...]
    # detailの作成
    detail = []
    for error in exc.errors():
        item = ValidationErrorResponseItem(
            loc=error["loc"],
            type=error["type"],
        )
        # クラスをJsonにして配列の中に入れている
        detail.append(item.model_dump())

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=ErrorResponse(detail=detail, type="VALIDATION_ERROR").model_dump(),
    )

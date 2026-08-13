from fastapi.requests import Request
from fastapi.responses import JSONResponse

from helpdesk_be.exceptions.business_exception import BusinessException
from helpdesk_be.schemas.response.v1.error import ErrorResponse


# BusinessExceptionをtype付きのErrorResponse形式に変換する。
# type="BUSINESS_ERROR"により、FE側はバリデーションエラー(type="VALIDATION_ERROR"、detailはlist)と
# 業務エラー(本ハンドラー、detailはstr)をtypeの値だけで判別できる
def handler(request: Request, exc: BusinessException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(detail=exc.detail, type="BUSINESS_ERROR").model_dump(),
    )

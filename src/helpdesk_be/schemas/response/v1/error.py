from helpdesk_be.schemas.response.v1.base import BaseV1ResponseSchema


class ValidationErrorResponseItem(BaseV1ResponseSchema):
    loc: list[str]
    type: str

class ErrorResponse(BaseV1ResponseSchema):
    detail: str | list[ValidationErrorResponseItem]
    type: str

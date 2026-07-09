from helpdesk_be.schemas.response.v1.base import BaseV1ResponseSchema


class LoginResponse(BaseV1ResponseSchema):
    message: str

from pydantic import EmailStr

from helpdesk_be.schemas.request.v1.base import BaseV1RequestSchema


class LoginRequest(BaseV1RequestSchema):
    email: EmailStr
    password: str

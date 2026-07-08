from pydantic import EmailStr, field_validator

from helpdesk_be.logic.business.password import user_password
from helpdesk_be.schemas.request.v1.base import BaseV1RequestSchema


# ユーザー新規登録APIのリクエストボディを表すスキーマ
# BaseV1RequestSchemaを継承することで、キャメルケースのJSON（例: {"email": ...}）を
# スネークケースのフィールドとして受け取れるようにしている
class LoginRequest(BaseV1RequestSchema):
    # EmailStr型にすることで、pydanticが自動でメールアドレス形式かどうかを検証する
    email: EmailStr
    # ハッシュ化前の生パスワード（DBにはそのまま保存せず、ロジック層でハッシュ化してから保存する）
    password: str

    # logic/validate/validate_password.pyの関数をpasswordフィールドのバリデータとして登録
    _validate_password = field_validator("password")(user_password)

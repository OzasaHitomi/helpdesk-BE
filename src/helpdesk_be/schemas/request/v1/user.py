from pydantic import EmailStr, field_validator

from helpdesk_be.logic.business.password import user_password
from helpdesk_be.schemas.request.v1.base import BaseV1RequestSchema
from helpdesk_be.store.enum.user_role_type import UserRoleType


# ユーザー新規登録APIのリクエストボディを表すスキーマ
# BaseV1RequestSchemaを継承することで、キャメルケースのJSON（例: {"email": ...}）を
# スネークケースのフィールドとして受け取れるようにしている
class CreateUserRequest(BaseV1RequestSchema):
    # usersテーブルのname(String(50))に合わせた氏名
    name: str
    # EmailStr型にすることで、pydanticが自動でメールアドレス形式かどうかを検証する
    email: EmailStr
    # ハッシュ化前の生パスワード（DBにはそのまま保存せず、ロジック層でハッシュ化してから保存する）
    password: str
    # このAPIで発行できるアカウントタイプは社員・サポート担当者のみ(ADMINはroute側でチェックする)
    role: UserRoleType

    # logic/validate/validate_password.pyの関数をpasswordフィールドのバリデータとして登録
    _validate_password = field_validator("password")(user_password)

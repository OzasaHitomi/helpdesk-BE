from pydantic import EmailStr, field_validator

from helpdesk_be.schemas.request.v1.base import BaseV1RequestSchema


# ユーザー新規登録APIのリクエストボディを表すスキーマ
# BaseV1RequestSchemaを継承することで、キャメルケースのJSON（例: {"email": ...}）を
# スネークケースのフィールドとして受け取れるようにしている
class LoginRequest(BaseV1RequestSchema):
    # EmailStr型にすることで、pydanticが自動でメールアドレス形式かどうかを検証する
    email: EmailStr
    # ハッシュ化前の生パスワード（DBにはそのまま保存せず、ロジック層でハッシュ化してから保存する）
    password: str

    # password単体に対するカスタムバリデーション
    # field_validatorで指定したフィールド（ここではpassword）に対して、
    # クラス定義時に自動で実行されるチェック処理を追加できる
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        # 8文字未満はNG
        if len(v) < 8:
            raise ValueError("パスワードは8文字以上で入力してください")
        # 数字を1文字も含まない場合はNG
        if not any(c.isdigit() for c in v):
            raise ValueError("パスワードには数字を1文字以上含めてください")
        # 大文字を1文字も含まない場合はNG
        if not any(c.isupper() for c in v):
            raise ValueError("パスワードには大文字を1文字以上含めてください")
        return v

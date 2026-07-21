from helpdesk_be.schemas.response.v1.base import BaseV1ResponseSchema
from helpdesk_be.store.enum.user_role_type import UserRoleType


# /meのレスポンス。password_hash等の内部情報を誤って含めないよう、
# 返却する項目をこのスキーマで明示的に絞り込む
class MeResponse(BaseV1ResponseSchema):
    id: int  # BE側でログイン中のユーザーを一意に特定するためのID
    role: UserRoleType  # FE側でユーザーのroleに応じて表示を出し分ける際に参照するroleの値

from helpdesk_be.schemas.response.v1.base import BaseV1ResponseSchema
from helpdesk_be.store.enum.user_role_type import UserRoleType

# フィールドの並びはmodels(User)の定義順に合わせる(password_hashは返却対象外)


# アカウント一覧APIの1件分のレスポンス
class GetUsersResponseItem(BaseV1ResponseSchema):
    id: int
    name: str
    email: str
    role: UserRoleType
    is_active: bool


# アカウント新規登録APIのレスポンス
class CreateUserResponse(BaseV1ResponseSchema):
    id: int
    name: str
    email: str
    role: UserRoleType
    is_active: bool

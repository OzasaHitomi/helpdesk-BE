from collections.abc import Callable
from typing import Annotated

from fastapi import Depends

from helpdesk_be.core.dependencies.auth import get_current_user
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.models.user import User
from helpdesk_be.store.enum.user_role_type import UserRoleType


# 指定したロールのいずれにも一致しない場合はForbiddenExceptionを送出する依存関数を生成する。
# 戻り値を使わない権限チェック専用のため、ルート関数の引数ではなく@router.xxx(dependencies=[Depends(...)])で使う想定
def require_role(*allowed_roles: UserRoleType, message: str) -> Callable[[User], None]:
    def check_role(user: Annotated[User, Depends(get_current_user)]) -> None:
        if user.role not in allowed_roles:
            raise ForbiddenException(message)

    return check_role

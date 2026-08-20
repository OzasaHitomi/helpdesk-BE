import pytest

from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.permission import require_role
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.store.enum.user_role_type import UserRoleType
from tests.factories.user_factory import create_user

# ------------------------------------------------------------------

# require_role: 指定したロールのいずれにも一致しない場合はForbiddenExceptionを送出する依存関数を生成する


# 正常系のテスト(許可したロールに一致する場合は例外を送出しない)
def test_require_role_does_not_raise_when_user_role_is_allowed(db_session: Session) -> None:
    user = create_user(db_session, role=UserRoleType.ADMIN)
    check_role = require_role(UserRoleType.ADMIN, message="管理者のみこの操作を実行できます")

    check_role(user)


# ------------------------


# 許可ロールを複数指定した場合、そのいずれかに一致すれば例外を送出しない
def test_require_role_does_not_raise_when_user_role_matches_one_of_multiple_allowed_roles(
    db_session: Session,
) -> None:
    user = create_user(db_session, role=UserRoleType.SUPPORT)
    check_role = require_role(
        UserRoleType.ADMIN,
        UserRoleType.SUPPORT,
        message="サポート担当、または管理者のみ実行できます",
    )

    check_role(user)


# ------------------------


# 異常系のテスト(許可したロールに一致しない場合は指定したメッセージで403)
def test_require_role_raises_forbidden_when_user_role_is_not_allowed(db_session: Session) -> None:
    user = create_user(db_session, role=UserRoleType.EMPLOYEE)
    check_role = require_role(UserRoleType.ADMIN, message="管理者のみこの操作を実行できます")

    with pytest.raises(ForbiddenException) as exc_info:
        check_role(user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "管理者のみこの操作を実行できます"

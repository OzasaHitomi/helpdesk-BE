from sqlalchemy.orm import Session

from helpdesk_be.repositories.user_repository import get_user_by_email
from helpdesk_be.store.enum.user_role_type import UserRoleType
from tests.factories.user_factory import create_user


def test_get_user_by_email_returns_matching_user(db_session: Session) -> None:
    # メールアドレスが一致するユーザーが存在する場合、そのユーザーが取得できることを確認する
    user = create_user(
        db_session,
        name="山田太郎",
        email="taro@example.com",
        role=UserRoleType.EMPLOYEE,
    )

    result = get_user_by_email(db_session, "taro@example.com")

    assert result is not None
    # emailはunique制約があるため一致確認だけで別ユーザー混入は起きない想定だが、念のため他の項目も作成したユーザーと一致するか確認する
    assert result.id == user.id
    assert result.name == user.name
    assert result.email == user.email
    assert result.role == user.role
    assert result.is_active == user.is_active


# ---------------------------------------------------------------------------------------


def test_get_user_by_email_returns_none_when_not_found(db_session: Session) -> None:
    # メールアドレスが一致するユーザーが存在しない場合、Noneが返ることを確認する
    result = get_user_by_email(db_session, "not_exist@example.com")

    assert result is None

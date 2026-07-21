from sqlalchemy.orm import Session

from helpdesk_be.repositories.user import get_user_by_email, get_user_by_id
from helpdesk_be.store.enum.user_role_type import UserRoleType
from tests.factories.user_factory import create_user

# ====================================================================
# get_user_by_email
# ====================================================================


def test_get_user_by_email_returns_matching_user(db_session: Session) -> None:
    # メールアドレスが一致するユーザーが存在する場合、そのユーザーが取得できることを確認する
    # 他のユーザーも登録しておくことで、単に1件しか存在しないから一致しているのではなく、
    # 複数件の中から正しく該当の1件を絞り込めていることを確認する
    create_user(db_session, name="鈴木花子", email="hanako@example.com")
    create_user(db_session, name="佐藤次郎", email="jiro@example.com")
    user = create_user(
        db_session,
        name="山田太郎",
        email="taro@example.com",
        role=UserRoleType.EMPLOYEE,
    )

    result = get_user_by_email(db_session, user.email)

    assert result is not None
    # emailはunique制約があるため一致確認だけで別ユーザー混入は起きない想定だが、念のため他の項目も作成したユーザーと一致するか確認する
    assert result.id == user.id
    assert result.name == user.name
    assert result.email == user.email
    assert result.role == user.role
    assert result.is_active == user.is_active


# ---------------------------------------------------------------------------------------


def test_get_user_by_email_returns_none_when_not_found(db_session: Session) -> None:
    # テーブルが空の場合でも、メールアドレスが一致するユーザーが存在しない場合、Noneが返ることを確認する
    result = get_user_by_email(db_session, "not_exist@example.com")

    assert result is None


# ---------------------------------------------------------------------------------------


def test_get_user_by_email_returns_none_when_email_does_not_match_existing_user(
    db_session: Session,
) -> None:
    # 別のメールアドレスのユーザーが存在する状態でも、
    # 一致しないメールアドレスで検索した場合はNoneが返る（絞り込みが正しく機能している）ことを確認する
    create_user(db_session, email="taro@example.com")

    result = get_user_by_email(db_session, "not_exist@example.com")

    assert result is None


# ====================================================================
# get_user_by_id
# ====================================================================


def test_get_user_by_id_returns_matching_user(db_session: Session) -> None:
    # ユーザーIDが一致するユーザーが存在する場合、そのユーザーが取得できることを確認する
    # 他のユーザーも登録しておくことで、単に1件しか存在しないから一致しているのではなく、
    # 複数件の中から正しく該当の1件を絞り込めていることを確認する
    create_user(db_session, name="鈴木花子", email="hanako@example.com")
    create_user(db_session, name="佐藤次郎", email="jiro@example.com")
    user = create_user(
        db_session,
        name="山田太郎",
        email="taro@example.com",
        role=UserRoleType.EMPLOYEE,
    )

    result = get_user_by_id(db_session, user.id)

    assert result is not None
    # idは主キーのため一致確認だけで別ユーザー混入は起きない想定だが、念のため他の項目も作成したユーザーと一致するか確認する
    assert result.id == user.id
    assert result.name == user.name
    assert result.email == user.email
    assert result.role == user.role
    assert result.is_active == user.is_active


# ---------------------------------------------------------------------------------------


def test_get_user_by_id_returns_none_when_not_found(db_session: Session) -> None:
    # テーブルが空の場合でも、ユーザーIDが一致するユーザーが存在しない場合、Noneが返ることを確認する
    result = get_user_by_id(db_session, 999)

    assert result is None


# ---------------------------------------------------------------------------------------


def test_get_user_by_id_returns_none_when_id_does_not_match_existing_user(
    db_session: Session,
) -> None:
    # 別のユーザーが存在する状態でも、
    # 一致しないIDで検索した場合はNoneが返る（絞り込みが正しく機能している）ことを確認する
    user = create_user(db_session, email="taro@example.com")

    result = get_user_by_id(db_session, user.id + 1)

    assert result is None

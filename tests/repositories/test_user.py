from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from helpdesk_be.repositories.user import (
    get_employee_and_support_users,
    get_user_by_email,
    get_user_by_id,
)
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


# ====================================================================
# get_employee_and_support_users
# ====================================================================


def test_get_employee_and_support_users_excludes_admin_accounts(
    db_session: Session,
) -> None:
    # 管理者(ログイン中管理者・別の管理者)は一覧に含まれず、社員・サポートのみ取得できることを確認する
    create_user(
        db_session, name="ログイン中管理者", email="admin_self@example.com", role=UserRoleType.ADMIN
    )
    create_user(
        db_session, name="別の管理者", email="admin_other@example.com", role=UserRoleType.ADMIN
    )
    employee = create_user(
        db_session, name="社員太郎", email="employee@example.com", role=UserRoleType.EMPLOYEE
    )
    support = create_user(
        db_session, name="サポート花子", email="support@example.com", role=UserRoleType.SUPPORT
    )

    result = get_employee_and_support_users(db_session)

    ids = {user.id for user in result}
    assert ids == {employee.id, support.id}


# ---------------------------------------------------------------------------------------


def test_get_employee_and_support_users_orders_by_created_at_desc(db_session: Session) -> None:
    # 作成日時(created_at)が新しい順に返ることを確認する
    old_user = create_user(
        db_session,
        name="古いユーザー",
        email="old@example.com",
        role=UserRoleType.EMPLOYEE,
        created_at=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Tokyo")),
    )
    new_user = create_user(
        db_session,
        name="新しいユーザー",
        email="new@example.com",
        role=UserRoleType.SUPPORT,
        created_at=datetime(2026, 7, 1, tzinfo=ZoneInfo("Asia/Tokyo")),
    )

    result = get_employee_and_support_users(db_session)

    assert [user.id for user in result] == [new_user.id, old_user.id]


# ---------------------------------------------------------------------------------------


def test_get_employee_and_support_users_returns_empty_list_when_only_admin_accounts_exist(
    db_session: Session,
) -> None:
    # 管理者しか存在しない場合は空リストが返ることを確認する
    create_user(db_session, role=UserRoleType.ADMIN)

    result = get_employee_and_support_users(db_session)

    assert result == []

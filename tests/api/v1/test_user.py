from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from helpdesk_be.store.enum.user_role_type import UserRoleType
from tests.factories.auth_factory import create_user_and_login
from tests.factories.user_factory import create_user

# ====================================================================
# GET /users
# ====================================================================

# リクエストの形式
# GET → パラメータなし
# レスポンスの形式
# 200 → 作成日時(created_at)降順の社員・サポートアカウント一覧(管理者は除く)を返す
# 403 → 管理者以外のロールでログイン中
#
# 未ログイン時の401はget_current_user依存関数自体の挙動（tests/core/dependencies/test_auth.pyで単体テスト済み）
# のため、ここでは重複してテストしない


# 対象アカウントが1件も無い場合は空配列が返る(社員・サポートが存在せず、管理者は元々一覧対象外)
def test_list_users_returns_empty_items_when_no_target_accounts_exist(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)

    response = client.get("/api/v1/users")

    assert response.status_code == 200
    assert response.json() == []


# ------------------------

# 管理者アカウントはログイン中の自分自身・別の管理者ともに一覧から除外され、社員・サポートはそれぞれ正しいroleで一覧に含まれる


def test_list_users_excludes_admin_accounts_and_includes_only_employee_and_support(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, name="ログイン中管理者", role=UserRoleType.ADMIN)
    create_user(
        db_session, name="別の管理者", email="other_admin@example.com", role=UserRoleType.ADMIN
    )
    create_user(
        db_session, name="社員花子", email="employee@example.com", role=UserRoleType.EMPLOYEE
    )
    create_user(
        db_session, name="サポート次郎", email="support@example.com", role=UserRoleType.SUPPORT
    )

    response = client.get("/api/v1/users")

    names_and_roles = {(item["name"], item["role"]) for item in response.json()}
    assert names_and_roles == {
        ("社員花子", UserRoleType.EMPLOYEE.value),
        ("サポート次郎", UserRoleType.SUPPORT.value),
    }


# ------------------------

# システム内表示名・Email・アカウントタイプ・利用状態がレスポンスに含まれる


def test_list_users_includes_account_fields(client: TestClient, db_session: Session) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)
    create_user(
        db_session,
        name="サポート次郎",
        email="support@example.com",
        role=UserRoleType.SUPPORT,
    )

    response = client.get("/api/v1/users")

    item = response.json()[0]
    assert item["name"] == "サポート次郎"
    assert item["email"] == "support@example.com"
    assert item["role"] == UserRoleType.SUPPORT.value
    assert item["isActive"] is True


# ------------------------

# 利用停止済み(is_active=False)のアカウントも一覧から除外されず、isActiveがfalseで返る


def test_list_users_includes_inactive_accounts_with_is_active_false(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)
    create_user(
        db_session,
        name="利用停止済み",
        email="inactive@example.com",
        role=UserRoleType.EMPLOYEE,
        is_active=False,
    )

    response = client.get("/api/v1/users")

    item = response.json()[0]
    assert item["isActive"] is False


# ------------------------

# 準正常系のテスト
# 管理者以外のロールでは一覧を取得できない


# 社員ロールの場合は403
def test_list_users_with_employee_role_returns_403(client: TestClient, db_session: Session) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.get("/api/v1/users")

    assert response.status_code == 403
    assert response.json()["detail"] == "管理者のみこの操作を実行できます"


# ------------------------


# サポート担当ロールの場合も403
def test_list_users_with_support_role_returns_403(client: TestClient, db_session: Session) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.SUPPORT)

    response = client.get("/api/v1/users")

    assert response.status_code == 403
    assert response.json()["detail"] == "管理者のみこの操作を実行できます"

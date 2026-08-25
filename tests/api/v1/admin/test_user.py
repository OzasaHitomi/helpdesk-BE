import pytest

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from helpdesk_be.logic.security.password import verify_password
from helpdesk_be.repositories.user import get_user_by_email
from helpdesk_be.store.enum.user_role_type import UserRoleType
from tests.conftest import RollbackTracker
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

    response = client.get("/api/v1/admin/users")

    assert response.status_code == 200
    assert response.json() == []


# ------------------------

# 管理者アカウントは一覧から除外され、社員・サポートはそれぞれ正しいroleで一覧に含まれる


def test_list_users_excludes_admin_accounts_and_includes_only_employee_and_support(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)
    create_user(
        db_session, name="社員花子", email="employee@example.com", role=UserRoleType.EMPLOYEE
    )
    create_user(
        db_session, name="サポート次郎", email="support@example.com", role=UserRoleType.SUPPORT
    )

    response = client.get("/api/v1/admin/users")

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

    response = client.get("/api/v1/admin/users")

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

    response = client.get("/api/v1/admin/users")

    item = response.json()[0]
    assert item["isActive"] is False


# ------------------------

# 準正常系のテスト
# 管理者以外のロールでは一覧を取得できない


# 社員ロールの場合は403
def test_list_users_with_employee_role_returns_403(client: TestClient, db_session: Session) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.get("/api/v1/admin/users")

    assert response.status_code == 403
    assert response.json()["detail"] == "管理者のみこの操作を実行できます"


# ------------------------


# サポート担当ロールの場合も403
def test_list_users_with_support_role_returns_403(client: TestClient, db_session: Session) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.SUPPORT)

    response = client.get("/api/v1/admin/users")

    assert response.status_code == 403
    assert response.json()["detail"] == "管理者のみこの操作を実行できます"


# ====================================================================
# POST /users
# ====================================================================

# リクエストの形式
# POST → name, email, password, role(employee/support)
# レスポンスの形式
# 201 → 作成したアカウント情報(id/name/email/role/isActive)を返す
# 403 → 管理者以外のロールでログイン中
# 422 → role=admin指定、パスワードが要件を満たさない、email重複のいずれか
# 500 → DB登録処理自体が失敗（コミットエラー）
#
# 未ログイン時の401はget_current_user依存関数自体の挙動（tests/core/dependencies/test_auth.pyで単体テスト済み）
# のため、ここでは重複してテストしない


# 社員・サポート担当アカウントを新規登録できる
@pytest.mark.parametrize(
    ("role", "name", "email"),
    [
        pytest.param(UserRoleType.EMPLOYEE, "社員花子", "employee@example.com", id="employee"),
        pytest.param(UserRoleType.SUPPORT, "サポート次郎", "support@example.com", id="support"),
    ],
)
def test_create_user_with_employee_or_support_role_returns_201(
    client: TestClient,
    db_session: Session,
    role: UserRoleType,
    name: str,
    email: str,
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)

    response = client.post(
        "/api/v1/admin/users",
        json={
            "name": name,
            "email": email,
            "password": "Password1",
            "role": role.value,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == name
    assert body["email"] == email
    assert body["role"] == role.value
    assert body["isActive"] is True


# ------------------------


# パスワードは平文で保存されず、bcryptハッシュ化された状態でDBに保存される
def test_create_user_stores_password_as_bcrypt_hash(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)

    response = client.post(
        "/api/v1/admin/users",
        json={
            "name": "社員花子",
            "email": "employee@example.com",
            "password": "Password1",
            "role": "employee",
        },
    )

    assert response.status_code == 201
    created_user = get_user_by_email(db_session, "employee@example.com")
    assert created_user is not None
    assert created_user.password_hash != "Password1"
    assert verify_password("Password1", created_user.password_hash) is True


# ------------------------

# 準正常系のテスト
# 管理者以外のロールでは新規登録できない


# 社員ロールの場合は403
def test_create_user_with_employee_login_returns_403(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.EMPLOYEE)

    response = client.post(
        "/api/v1/admin/users",
        json={
            "name": "社員花子",
            "email": "employee@example.com",
            "password": "Password1",
            "role": "employee",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "管理者のみこの操作を実行できます"


# ------------------------


# サポート担当ロールの場合も403
def test_create_user_with_support_login_returns_403(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.SUPPORT)

    response = client.post(
        "/api/v1/admin/users",
        json={
            "name": "社員花子",
            "email": "employee@example.com",
            "password": "Password1",
            "role": "employee",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "管理者のみこの操作を実行できます"


# ------------------------

# 異常系のテスト


# roleにadminを指定した場合は422(このAPIでは社員・サポート担当者のみ発行できる)
def test_create_user_with_admin_role_returns_422(client: TestClient, db_session: Session) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)

    response = client.post(
        "/api/v1/admin/users",
        json={
            "name": "管理者太郎",
            "email": "admin2@example.com",
            "password": "Password1",
            "role": "admin",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "要望のアカウント種別は作成できません"


# ------------------------


# パスワードが要件(8文字以上・数字・大文字を含む)を満たさない場合は422
# 各要件の判定ロジック自体はtests/logic/business/test_password.pyで単体テスト済みのため、
# ここではfield_validatorとして正しく組み込まれ422が返ることのみ確認する
def test_create_user_with_too_short_password_returns_422(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)

    response = client.post(
        "/api/v1/admin/users",
        json={
            "name": "社員花子",
            "email": "employee@example.com",
            "password": "Pass1",
            "role": "employee",
        },
    )

    assert response.status_code == 422


# ------------------------


# 既に存在するメールアドレスを指定した場合は422
def test_create_user_with_duplicate_email_returns_422(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)
    create_user(db_session, name="社員花子", email="employee@example.com")

    response = client.post(
        "/api/v1/admin/users",
        json={
            "name": "社員次郎",
            "email": "employee@example.com",
            "password": "Password1",
            "role": "employee",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "このメールアドレスは既に登録されています"


# ------------------------


# DB登録処理自体が失敗した場合は500・rollbackが呼ばれる
def test_create_user_returns_500_when_commit_fails(
    db_session: Session,
    client_with_commit_error: TestClient,
    rollback_tracker: RollbackTracker,
) -> None:
    create_user_and_login(db_session, client_with_commit_error, role=UserRoleType.ADMIN)

    response = client_with_commit_error.post(
        "/api/v1/admin/users",
        json={
            "name": "社員花子",
            "email": "employee@example.com",
            "password": "Password1",
            "role": "employee",
        },
    )

    assert response.status_code == 500
    assert rollback_tracker.called is True


# ====================================================================
# PUT /users/{user_id}/deactivate
# ====================================================================

# リクエストの形式
# PUT → パラメータなし
# レスポンスの形式
# 200 → 利用停止後のアカウント情報(id/name/email/role/isActive)を返す
# 403 → 管理者以外のロールでログイン中
# 404 → 対象ユーザーが存在しない、または対象が管理者ロールのいずれか
# 422 → 対象が既に利用停止済み
# 500 → DB更新処理自体が失敗(コミットエラー)
#
# 未ログイン時の401はget_current_user依存関数自体の挙動（tests/core/dependencies/test_auth.pyで単体テスト済み）
# のため、ここでは重複してテストしない


# 社員・サポート担当アカウントを利用停止にできる
@pytest.mark.parametrize(
    ("role", "name", "email"),
    [
        pytest.param(UserRoleType.EMPLOYEE, "社員花子", "employee@example.com", id="employee"),
        pytest.param(UserRoleType.SUPPORT, "サポート次郎", "support@example.com", id="support"),
    ],
)
def test_deactivate_user_returns_200(
    client: TestClient,
    db_session: Session,
    role: UserRoleType,
    name: str,
    email: str,
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)
    target_user = create_user(db_session, name=name, email=email, role=role)

    response = client.put(f"/api/v1/admin/users/{target_user.id}/deactivate")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == name
    assert body["email"] == email
    assert body["role"] == role.value
    assert body["isActive"] is False


# ------------------------

# 準正常系のテスト
# 管理者以外のロールでは利用停止にできない


# 社員・サポート担当ロールの場合は403
@pytest.mark.parametrize(
    ("login_role"),
    [
        pytest.param(UserRoleType.EMPLOYEE, id="employee"),
        pytest.param(UserRoleType.SUPPORT, id="support"),
    ],
)
def test_deactivate_user_with_non_admin_login_returns_403(
    client: TestClient,
    db_session: Session,
    login_role: UserRoleType,
) -> None:
    create_user_and_login(db_session, client, role=login_role)
    target_user = create_user(db_session, name="社員花子", email="employee@example.com")

    response = client.put(f"/api/v1/admin/users/{target_user.id}/deactivate")

    assert response.status_code == 403
    assert response.json()["detail"] == "管理者のみこの操作を実行できます"


# ------------------------

# 異常系のテスト


# 存在しないuser_idを指定した場合、対象が管理者ロールの場合(存在を推測させないため)いずれも404
@pytest.mark.parametrize(
    ("target_is_admin"),
    [
        pytest.param(False, id="nonexistent_id"),
        pytest.param(True, id="admin_target"),
    ],
)
def test_deactivate_user_returns_404(
    client: TestClient,
    db_session: Session,
    target_is_admin: bool,
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)
    if target_is_admin:
        target_user = create_user(
            db_session, name="管理者次郎", email="admin2@example.com", role=UserRoleType.ADMIN
        )
        target_user_id = target_user.id
    else:
        target_user_id = 9999

    response = client.put(f"/api/v1/admin/users/{target_user_id}/deactivate")

    assert response.status_code == 404
    assert response.json()["detail"] == "ユーザーが見つかりません"


# ------------------------


# 既に利用停止済みのユーザーを指定した場合は422
def test_deactivate_user_with_already_inactive_target_returns_422(
    client: TestClient, db_session: Session
) -> None:
    create_user_and_login(db_session, client, role=UserRoleType.ADMIN)
    target_user = create_user(
        db_session,
        name="社員花子",
        email="employee@example.com",
        is_active=False,
    )

    response = client.put(f"/api/v1/admin/users/{target_user.id}/deactivate")

    assert response.status_code == 422
    assert response.json()["detail"] == "既に利用停止済みのユーザーです"


# ------------------------


# DB更新処理自体が失敗した場合は500・rollbackが呼ばれる
def test_deactivate_user_returns_500_when_commit_fails(
    db_session: Session,
    client_with_commit_error: TestClient,
    rollback_tracker: RollbackTracker,
) -> None:
    create_user_and_login(db_session, client_with_commit_error, role=UserRoleType.ADMIN)
    target_user = create_user(db_session, name="社員花子", email="employee@example.com")

    response = client_with_commit_error.put(f"/api/v1/admin/users/{target_user.id}/deactivate")

    assert response.status_code == 500
    assert rollback_tracker.called is True

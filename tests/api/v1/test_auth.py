from datetime import UTC, datetime, timedelta

import jwt as pyjwt

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from helpdesk_be.core.config.base import core_settings
from helpdesk_be.logic.security.jwt import (
    AccessTokenPayload,
    create_access_token,
    verify_access_token,
)
from helpdesk_be.logic.security.password import hash_password
from helpdesk_be.store.enum.user_role_type import UserRoleType
from tests.factories.user_factory import create_user

# ====================================================================
# POST /auth
# ====================================================================

# リクエストの形式
# POST → リクエストボディ（json）でemail/passwordを送る
# レスポンスの形式
# 204 → ログイン成功（ボディなし）＋Cookieにアクセストークンが設定される
# 401 → メールアドレスが存在しない／パスワード不一致
# 403 → 認証情報は正しいが利用停止中


# 正常系のテストpost（ログイン成功）
def test_login_success(client: TestClient, db_session: Session) -> None:
    user = create_user(
        db_session, email="taro@example.com", password_hash=hash_password("Password1")
    )

    response = client.post(
        "/api/v1/auth",
        json={"email": "taro@example.com", "password": "Password1"},
    )
    assert response.status_code == 204
    # 204はボディなしのはずなので、レスポンスボディ(bytes)が空であることを確認する
    assert response.content == b""

    # Cookieにアクセストークンが設定され、payloadにユーザーIDとroleが含まれていること
    access_token = response.cookies.get("access_token")
    assert access_token is not None
    payload = verify_access_token(access_token)
    assert payload["sub"] == str(user.id)
    assert payload["role"] == user.role.value


# ------------------------

# 準正常系・異常系のテストpost
# ログイン失敗のパターンは3つ（ユーザー未存在／パスワード不一致／利用停止中）


# ユーザーが存在しない場合は401
def test_login_with_not_found_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth",
        json={"email": "not_exist@example.com", "password": "Password1"},
    )
    assert response.status_code == 401

    data = response.json()
    assert data["detail"] == "メールアドレスまたはパスワードが正しくありません"


# ------------------------


# パスワードが一致しない場合も、ユーザー未存在時と同じ401・同じメッセージ
def test_login_with_wrong_password(client: TestClient, db_session: Session) -> None:
    create_user(db_session, email="taro@example.com", password_hash=hash_password("Password1"))

    response = client.post(
        "/api/v1/auth",
        json={"email": "taro@example.com", "password": "WrongPass1"},
    )
    assert response.status_code == 401

    data = response.json()
    assert data["detail"] == "メールアドレスまたはパスワードが正しくありません"


# ------------------------


# 認証情報は正しいが利用停止中のユーザーの場合は403
def test_login_with_inactive_user(client: TestClient, db_session: Session) -> None:
    create_user(
        db_session,
        email="taro@example.com",
        password_hash=hash_password("Password1"),
        is_active=False,
    )

    response = client.post(
        "/api/v1/auth",
        json={"email": "taro@example.com", "password": "Password1"},
    )
    assert response.status_code == 403

    data = response.json()
    assert data["detail"] == "このアカウントは現在ご利用いただけません"


# ====================================================================
# GET /me
# ====================================================================

# リクエストの形式
# GET → Cookieのaccess_token（ログインセッション）のみで認証する。リクエストボディは無し
# レスポンスの形式
# 200 → ログイン中のユーザー情報（id, role）
# 401 → 未ログイン（Cookie無し／不正なトークン／期限切れ）
# 403 → ログイン済みだが利用停止中


# 正常系のテスト（社員ロールでログイン済みの場合、200でユーザー情報が返る）
def test_me_success_for_employee(client: TestClient, db_session: Session) -> None:
    user = create_user(
        db_session,
        name="山田太郎",
        email="taro@example.com",
        role=UserRoleType.EMPLOYEE,
    )
    access_token = create_access_token(AccessTokenPayload(sub=str(user.id), role=user.role))
    client.cookies.set("access_token", access_token)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user.id
    assert data["role"] == user.role.value


# ------------------------


# 正常系のテスト（サポートロール・アクティブなユーザーの場合、roleがsupportとして返る）
def test_me_success_for_active_support_user(client: TestClient, db_session: Session) -> None:
    user = create_user(
        db_session,
        name="鈴木花子",
        email="hanako@example.com",
        role=UserRoleType.SUPPORT,
        is_active=True,
    )
    access_token = create_access_token(AccessTokenPayload(sub=str(user.id), role=user.role))
    client.cookies.set("access_token", access_token)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["role"] == "support"


# ------------------------


# 正常系のテスト（管理者ロール・アクティブなユーザーの場合、roleがadminとして返る）
def test_me_success_for_active_admin_user(client: TestClient, db_session: Session) -> None:
    user = create_user(
        db_session,
        name="佐藤次郎",
        email="jiro@example.com",
        role=UserRoleType.ADMIN,
        is_active=True,
    )
    access_token = create_access_token(AccessTokenPayload(sub=str(user.id), role=user.role))
    client.cookies.set("access_token", access_token)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


# ------------------------

# 準正常系・異常系のテスト
# 認証エラーのパターン（Cookie無し／不正なトークン／期限切れは401、利用停止中は403）
#
# これらはget_current_user依存関数自体の挙動（tests/core/dependencies/test_auth.pyで単体テスト済み）を
# GET /meというエンドポイント経由で再確認しているものであり、get_current_userを使う他のAPIを実装する際に
# 同様の異常系テストを重複して用意する必要はない


# Cookieが無い場合は401
def test_me_without_cookie_returns_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "ログインが必要です"


# ------------------------


# Cookieの値が不正なトークンの場合も401
def test_me_with_invalid_token_returns_401(client: TestClient) -> None:
    client.cookies.set("access_token", "invalid-token")

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "ログインが必要です"


# ------------------------


# トークンの有効期限が切れている場合も401
def test_me_with_expired_token_returns_401(client: TestClient, db_session: Session) -> None:
    user = create_user(db_session, email="taro@example.com")
    expired_token = pyjwt.encode(
        {
            "sub": str(user.id),
            "role": user.role.value,
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        core_settings.jwt_secret_key,
        algorithm=core_settings.jwt_algorithm,
    )

    client.cookies.set("access_token", expired_token)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "セッションの有効期限が切れました。再度ログインしてください"


# ------------------------


# サポートロールでも利用停止中のユーザーの場合は403
# （ログインAPI自体は停止中ユーザーを弾くため、正規ログイン後にアカウントが停止された想定でトークンを直接発行する）
def test_me_with_inactive_support_user_returns_403(client: TestClient, db_session: Session) -> None:
    user = create_user(
        db_session,
        name="高橋一郎",
        email="ichiro@example.com",
        role=UserRoleType.SUPPORT,
        is_active=False,
    )
    access_token = create_access_token(AccessTokenPayload(sub=str(user.id), role=user.role))
    client.cookies.set("access_token", access_token)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 403
    assert response.json()["detail"] == "このアカウントは現在ご利用いただけません"

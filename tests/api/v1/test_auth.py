from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from helpdesk_be.logic.security.jwt import verify_access_token
from helpdesk_be.logic.security.password import hash_password
from tests.factories.user_factory import create_user

# ------------------------------------------------------------------

# リクエストの形式
# POST はリクエストボディ（json=）でデータを送る:
# レスポンスの形式
# POST → 成功メッセージ＋Cookieにアクセストークンが設定される:


# 正常系のテストpost（ログイン成功）
def test_login_success(client: TestClient, db_session: Session) -> None:
    user = create_user(
        db_session, email="taro@example.com", password_hash=hash_password("Password1")
    )

    response = client.post(
        "/api/v1/auth",
        json={"email": "taro@example.com", "password": "Password1"},
    )
    assert response.status_code == 200

    data = response.json()
    assert data["message"] == "ログインに成功しました"

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

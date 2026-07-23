from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from helpdesk_be.logic.security.jwt import AccessTokenPayload, create_access_token
from helpdesk_be.models.user import User
from tests.factories.user_factory import create_user


# 指定したuserでアクセストークンを作成し、clientのCookieにセットする（ログイン済み状態を再現するテスト用メソッド）
def set_login_cookie(client: TestClient, user: User) -> str:
    access_token = create_access_token(AccessTokenPayload(sub=str(user.id), role=user.role))
    client.cookies.set("access_token", access_token, domain=client.base_url.host)
    return access_token


# ユーザー作成とログイン済み状態の再現（Cookieセット）をまとめて行うメソッド
def create_user_and_login(db_session: Session, client: TestClient, **update_data: object) -> User:
    user = create_user(db_session, **update_data)
    set_login_cookie(client, user)
    return user

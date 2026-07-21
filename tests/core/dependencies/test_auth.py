from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from sqlalchemy.orm import Session

from helpdesk_be.core.config.base import core_settings
from helpdesk_be.core.dependencies.auth import get_current_user
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.exceptions.unauthorized_exception import UnauthorizedException
from helpdesk_be.logic.security.jwt import AccessTokenPayload, create_access_token
from helpdesk_be.store.enum.user_role_type import UserRoleType
from tests.factories.user_factory import create_user

# ------------------------------------------------------------------

# get_current_user: Cookieのaccess_token（JWT）を検証し、DBから現在のユーザーを取得する依存関数
#
# 各テストは検証対象のメソッド自身の結果に依存しないよう、
# 対になるトークンの生成はpyjwt（インストール済みパッケージ）で行う


# 正常系のテスト（有効なトークンから対応するユーザーが取得できる）
def test_get_current_user_returns_user_for_valid_token(db_session: Session) -> None:
    user = create_user(db_session, email="taro@example.com", role=UserRoleType.SUPPORT)
    access_token = create_access_token(AccessTokenPayload(sub=str(user.id), role=user.role))

    result = get_current_user(session=db_session, access_token=access_token)

    assert result.id == user.id
    assert result.role == user.role


# ------------------------


# 異常系のテスト（Cookie自体が無い場合は401「ログインが必要です」）
def test_get_current_user_raises_unauthorized_when_token_missing(db_session: Session) -> None:
    with pytest.raises(UnauthorizedException) as exc_info:
        get_current_user(session=db_session, access_token=None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "ログインが必要です"


# ------------------------


# 異常系のテスト（トークンがデコードできない不正な文字列の場合も401「ログインが必要です」）
def test_get_current_user_raises_unauthorized_when_token_malformed(db_session: Session) -> None:
    with pytest.raises(UnauthorizedException) as exc_info:
        get_current_user(session=db_session, access_token="invalid-token")

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "ログインが必要です"


# ------------------------


# 異常系のテスト（署名が改ざんされている場合も401「ログインが必要です」）
def test_get_current_user_raises_unauthorized_when_signature_invalid(db_session: Session) -> None:
    tampered_token = pyjwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) + timedelta(minutes=10)},
        "other-secret-key-with-enough-length-for-hs256",
        algorithm=core_settings.jwt_algorithm,
    )

    with pytest.raises(UnauthorizedException) as exc_info:
        get_current_user(session=db_session, access_token=tampered_token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "ログインが必要です"


# ------------------------


# 異常系のテスト（トークンの有効期限切れの場合は、一度はログインに成功しているため
# 「ログインが必要です」ではなく期限切れである旨のメッセージを401で返す）
def test_get_current_user_raises_unauthorized_when_token_expired(db_session: Session) -> None:
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

    with pytest.raises(UnauthorizedException) as exc_info:
        get_current_user(session=db_session, access_token=expired_token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "セッションの有効期限が切れました。再度ログインしてください"


# ------------------------


# 異常系のテスト（署名・有効期限は正しいが、subに対応するユーザーがDBに存在しない場合も
# 401「ログインが必要です」。現状は退会機能が無いため実際には発生しない防御的チェック）
def test_get_current_user_raises_unauthorized_when_user_not_found(db_session: Session) -> None:
    access_token = create_access_token(AccessTokenPayload(sub="999999", role=UserRoleType.EMPLOYEE))

    with pytest.raises(UnauthorizedException) as exc_info:
        get_current_user(session=db_session, access_token=access_token)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "ログインが必要です"


# ------------------------


# 異常系のテスト（トークンは有効だが利用停止中の場合は、loginエンドポイントの
# 利用停止時と同じ403「このアカウントは現在ご利用いただけません」を返す）
def test_get_current_user_raises_forbidden_when_user_inactive(db_session: Session) -> None:
    user = create_user(db_session, email="taro@example.com", is_active=False)
    access_token = create_access_token(AccessTokenPayload(sub=str(user.id), role=user.role))

    with pytest.raises(ForbiddenException) as exc_info:
        get_current_user(session=db_session, access_token=access_token)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "このアカウントは現在ご利用いただけません"

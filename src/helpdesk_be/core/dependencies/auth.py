from typing import Annotated

import jwt

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.exceptions.unauthorized_exception import UnauthorizedException
from helpdesk_be.logic.security.jwt import verify_access_token
from helpdesk_be.models.user import User
from helpdesk_be.repositories.user import get_user_by_id


# Cookieのaccess_token（JWT）を検証し、ペイロードのユーザーIDをもとにDBから現在のユーザーを取得する依存関数。
# 認証が必要な複数のエンドポイントで共通して使えるよう、Dependsとして切り出している。
# Cookie無し・署名不正・期限切れ・ユーザー不在・利用停止中のいずれの場合も
# 呼び出し元に理由を区別させず、一律で401 Unauthorizedを返す
# （区別して返すと、正規の利用者以外にアカウントの存在有無や状態を推測する手がかりを与えてしまうため）
def get_current_user(
    session: Annotated[Session, Depends(get_db)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    if access_token is None:
        raise UnauthorizedException("ログインが必要です")

    try:
        payload = verify_access_token(access_token)
    except jwt.InvalidTokenError as e:
        raise UnauthorizedException("ログインが必要です") from e

    user = get_user_by_id(session, int(payload["sub"]))

    if user is None or not user.is_active:
        raise UnauthorizedException("ログインが必要です")

    return user

from typing import Annotated

import jwt

from fastapi import Cookie, Depends
from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.exceptions.unauthorized_exception import UnauthorizedException
from helpdesk_be.logic.security.jwt import verify_access_token
from helpdesk_be.models.user import User
from helpdesk_be.repositories.user import get_user_by_id


# Cookieのaccess_token（JWT）を検証し、ペイロードのユーザーIDをもとにDBから現在のユーザーを取得する依存関数。
# 認証が必要な複数のエンドポイントで共通して使えるよう、Dependsとして切り出している。
# Cookie無し・署名不正・ユーザー不在はアカウントの存在有無を推測されないよう一律「ログインが必要です」で401を返すが、
# 期限切れ・利用停止中はCookie自体は正当な形で存在している（＝一度はログインできていた）状況のため、
# FEが適切な案内（再ログインを促す／利用停止である旨を伝える）を出し分けられるよう理由ごとに返却内容を分ける
def get_current_user(
    session: Annotated[Session, Depends(get_db)],
    access_token: Annotated[str | None, Cookie()] = None,
) -> User:
    if access_token is None:
        raise UnauthorizedException("ログインが必要です")

    try:
        payload = verify_access_token(access_token)
    except jwt.ExpiredSignatureError as e:
        raise UnauthorizedException(
            "セッションの有効期限が切れました。再度ログインしてください"
        ) from e
    except jwt.InvalidTokenError as e:
        raise UnauthorizedException("ログインが必要です") from e

    user = get_user_by_id(session, int(payload["sub"]))

    if user is None:
        raise UnauthorizedException("ログインが必要です")

    if not user.is_active:
        raise ForbiddenException("このアカウントは現在ご利用いただけません")

    return user

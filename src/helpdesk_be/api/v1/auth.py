from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from helpdesk_be.core.config.base import core_settings
from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.exceptions.unauthorized_exception import UnauthorizedException
from helpdesk_be.logic.security.jwt import create_access_token
from helpdesk_be.logic.security.password import verify_password
from helpdesk_be.repositories.user_repository import get_user_by_email
from helpdesk_be.schemas.request.v1.auth import LoginRequest
from helpdesk_be.schemas.response.v1.auth import LoginResponse

router = APIRouter()

# メール未登録／パスワード不一致のどちらでも同じメッセージにし、
# レスポンス差異からメールアドレスの存在を推測されないようにする
INVALID_CREDENTIALS_MESSAGE = "メールアドレスまたはパスワードが正しくありません"


@router.post("", response_model=LoginResponse)
def login(
    body: LoginRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
) -> LoginResponse:
    # ユーザーを検索する(emailの一致)
    user = get_user_by_email(session, body.email)

    # ユーザーが存在しない場合も、パスワード不一致時と同じエラーを返す
    if user is None:
        raise UnauthorizedException(INVALID_CREDENTIALS_MESSAGE)

    # パスワードを照合する（不正アクセス防止のため）
    if not verify_password(body.password, user.password_hash):
        raise UnauthorizedException(INVALID_CREDENTIALS_MESSAGE)

    # 利用可能なユーザーか確認する。
    # パスワード照合より前にこの確認を行うと、「利用不可」というレスポンス差異から
    # メールアドレスの存在有無を総当たりで探られてしまうため、照合後に行う
    if not user.is_active:
        raise ForbiddenException("このアカウントは現在ご利用いただけません")

    # JWTを生成する（ユーザーIDとロールをペイロードに含める）
    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})

    # Cookieの設定
    # httponly=TrueでJS経由のアクセスを防止、samesite=laxでCSRFのリスクを抑制
    # ⭐️secure=False（開発環境がhttpのため）。本番環境（https）ではTrueに変更すること
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=core_settings.jwt_expire_minutes * 60,
    )

    # レスポンスを返す
    return LoginResponse(message="ログインに成功しました")

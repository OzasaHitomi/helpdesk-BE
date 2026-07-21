from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from helpdesk_be.core.config.base import core_settings
from helpdesk_be.core.dependencies.auth import get_current_user
from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.exceptions.unauthorized_exception import UnauthorizedException
from helpdesk_be.logic.security.jwt import AccessTokenPayload, create_access_token
from helpdesk_be.logic.security.password import verify_password
from helpdesk_be.models.user import User
from helpdesk_be.repositories.user import get_user_by_email
from helpdesk_be.schemas.request.v1.auth import LoginRequest
from helpdesk_be.schemas.response.v1.auth import MeResponse

router = APIRouter()


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
def login(
    body: LoginRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db)],
) -> None:
    # ユーザーを検索する(emailの一致)
    user = get_user_by_email(session, body.email)

    # ユーザーが存在しない場合とパスワード不一致の場合は同じエラーを返す（不正アクセス防止のため）。
    # user is Noneを先に評価することで、Noneの場合はverify_passwordを実行しない（短絡評価）
    if user is None or not verify_password(body.password, user.password_hash):
        raise UnauthorizedException("メールアドレスまたはパスワードが正しくありません")

    # 利用可能なユーザーか確認する。
    # パスワード照合より前にこの確認を行うと、「利用不可」というレスポンス差異から
    # メールアドレスの存在有無を総当たりで探られてしまうため、照合後に行う
    if not user.is_active:
        raise ForbiddenException("このアカウントは現在ご利用いただけません")

    # JWTを生成する（ユーザーIDとロールをペイロードに含める）
    access_token = create_access_token(AccessTokenPayload(sub=str(user.id), role=user.role))

    # Cookieの設定
    # httponly=TrueでJS経由のアクセスを防止、samesite=laxでCSRFのリスクを抑制
    # ⭐️secure=False（開発環境がhttpのため）。本番環境（https）ではTrueに変更すること
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        # Cookieの有効期限をJWTの有効期限と揃えるため、同じjwt_expire_minutesを使う
        # （max_ageは秒指定のため、分の値を60倍して秒に変換している）
        max_age=core_settings.jwt_expire_minutes * 60,
    )

    return None


# ------------------------------------------------------------------


@router.get("/me")
def get_me(user: Annotated[User, Depends(get_current_user)]) -> MeResponse:
    # get_current_userがCookieの検証・ユーザー取得・利用停止チェックまで済ませているため、
    # ここではユーザー情報をレスポンス用スキーマに詰めるだけでよい
    return MeResponse(id=user.id, name=user.name, email=user.email, role=user.role)

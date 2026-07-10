from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

import jwt

from helpdesk_be.core.config.base import core_settings
from helpdesk_be.store.enum.user_role_type import UserRoleType


# アクセストークンに含める情報を型として定義する。
# dict[str, Any]で受け取る形にすると、キー名も値の型も呼び出し側の自由になってしまい、
# 「アクセストークンに必要な情報は何か」という契約をコード上で保証できないため、
# create_access_tokenの引数をこの型に限定することでキー名・型の誤りを防ぐ
# frozen=Trueにして生成後に値を書き換えられないようにする
# （トークンに埋め込む値をその場で渡すだけの入れ物であり、生成後に書き換える必要がないため）
@dataclass(frozen=True)
class AccessTokenPayload:
    sub: str
    role: UserRoleType


def create_access_token(payload: AccessTokenPayload) -> str:
    # 有効期限(exp)を付与する。これがないとトークンが漏洩した場合に永久に使われ続けてしまう
    # logic層内での責務違反(logicから別logicの呼び出し)を避けるため、calc_datetime.get_nowは使わずここで直接取得する
    now = datetime.now(ZoneInfo("Asia/Tokyo"))
    to_encode = {
        "sub": payload.sub,
        "role": payload.role.value,
        "exp": now + timedelta(minutes=core_settings.jwt_expire_minutes),
    }
    # payloadを秘密鍵で署名し、JWT文字列（ヘッダー.ペイロード.署名 の3つをつなげた文字列）を生成する
    # 秘密鍵を知っている（=自分のサーバーだけが持っている）ことで、後から偽造されていないかを検証できる
    return jwt.encode(
        to_encode, core_settings.jwt_secret_key, algorithm=core_settings.jwt_algorithm
    )


def verify_access_token(token: str) -> dict[str, Any]:
    # 秘密鍵を使って署名を検証し、改ざんされていなければpayloadを復元する
    # 署名が不正な場合はjwt.InvalidTokenError（の派生クラス）が送出される
    # 呼び出し元でtry/exceptして、401 Unauthorizedなどに変換することを想定している
    return jwt.decode(token, core_settings.jwt_secret_key, algorithms=[core_settings.jwt_algorithm])

from typing import Any

import jwt

from helpdesk_be.core.config.base import core_settings


def create_access_token(payload: dict[str, Any]) -> str:
    # payloadを秘密鍵で署名し、JWT文字列（ヘッダー.ペイロード.署名 の3つをつなげた文字列）を生成する
    # 秘密鍵を知っている（=自分のサーバーだけが持っている）ことで、後から偽造されていないかを検証できる
    return jwt.encode(payload, core_settings.jwt_secret_key, algorithm=core_settings.jwt_algorithm)


def verify_access_token(token: str) -> dict[str, Any]:
    # 秘密鍵を使って署名を検証し、改ざんされていなければpayloadを復元する
    # 署名が不正な場合はjwt.InvalidTokenError（の派生クラス）が送出される
    # 呼び出し元でtry/exceptして、401 Unauthorizedなどに変換することを想定している
    return jwt.decode(token, core_settings.jwt_secret_key, algorithms=[core_settings.jwt_algorithm])


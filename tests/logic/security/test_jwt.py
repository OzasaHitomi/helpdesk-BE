from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from freezegun import freeze_time

from helpdesk_be.core.config.base import core_settings
from helpdesk_be.logic.security.jwt import (
    AccessTokenPayload,
    create_access_token,
    verify_access_token,
)
from helpdesk_be.store.enum.user_role_type import UserRoleType

# ------------------------------------------------------------------

# create_access_token: payloadを署名してJWT文字列を生成する
# verify_access_token: 署名を検証してpayloadを復元する。不正なトークンの場合は例外を送出する
#
# 各テストは検証対象のメソッド自身の結果に依存しないよう、
# 対になるトークンの生成・検証はpyjwt（インストール済みパッケージ）で行う


# ============================================================
# create_access_token
# ============================================================


# 正常系のテスト（payloadの内容・有効期限(exp)・署名鍵が正しくJWTにエンコードされる）
# 確認内容:
# - payloadの内容（sub, role）がそのままエンコードされる
# - exp（有効期限）が「現在時刻 + jwt_expire_minutes」の値で設定される
# - core_settings.jwt_secret_keyで署名される（異なる秘密鍵でデコードするとInvalidSignatureError）
@freeze_time("2026-05-01 12:00:00+00:00")
def test_create_access_token_encodes_payload_expiration_and_signature() -> None:
    payload = AccessTokenPayload(sub="1", role=UserRoleType.EMPLOYEE)

    token = create_access_token(payload)
    decoded = pyjwt.decode(
        token, core_settings.jwt_secret_key, algorithms=[core_settings.jwt_algorithm]
    )

    # payloadの内容がそのままエンコードされていること
    assert decoded["sub"] == "1"
    assert decoded["role"] == "employee"

    # expが「現在時刻 + jwt_expire_minutes」の値で設定されていること
    expected_exp = int(datetime(2026, 5, 1, 12, 0, 0, tzinfo=UTC).timestamp())
    expected_exp += core_settings.jwt_expire_minutes * 60
    assert decoded["exp"] == expected_exp

    # core_settings.jwt_secret_keyで署名されていること
    with pytest.raises(pyjwt.InvalidSignatureError):
        pyjwt.decode(
            token,
            "other-secret-key-with-enough-length-for-hs256",
            algorithms=[core_settings.jwt_algorithm],
        )


# ============================================================
# verify_access_token
# ============================================================


# 正常系のテスト（署名済みトークンからpayloadを復元できる）
def test_verify_access_token_returns_payload_for_valid_token() -> None:
    # pyjwt.encodeで直接組み立てたトークンを検証し、payloadの内容が
    # そのまま復元できることを確認する
    exp = datetime.now(UTC) + timedelta(minutes=10)
    token = pyjwt.encode(
        {"sub": "1", "role": "employee", "exp": exp},
        core_settings.jwt_secret_key,
        algorithm=core_settings.jwt_algorithm,
    )

    result = verify_access_token(token)

    assert result["sub"] == "1"
    assert result["role"] == "employee"


# ------------------------


# 異常系のテスト（有効期限切れ）
def test_verify_access_token_raises_when_expired() -> None:
    # 有効期限切れのトークンを検証すると、jwt.ExpiredSignatureErrorが送出されることを確認する
    expired_exp = datetime.now(UTC) - timedelta(minutes=1)
    token = pyjwt.encode(
        {"sub": "1", "exp": expired_exp},
        core_settings.jwt_secret_key,
        algorithm=core_settings.jwt_algorithm,
    )

    with pytest.raises(pyjwt.ExpiredSignatureError):
        verify_access_token(token)


# ------------------------


# 異常系のテスト（署名が不正・改ざんされている）
def test_verify_access_token_raises_when_signature_invalid() -> None:
    # 別の秘密鍵で署名された（改ざんされた想定の）トークンを検証すると、
    # jwt.InvalidSignatureErrorが送出されることを確認する
    tampered_token = pyjwt.encode(
        {"sub": "1"},
        "other-secret-key-with-enough-length-for-hs256",
        algorithm=core_settings.jwt_algorithm,
    )

    with pytest.raises(pyjwt.InvalidSignatureError):
        verify_access_token(tampered_token)

from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest

from freezegun import freeze_time

from helpdesk_be.core.config.base import core_settings
from helpdesk_be.logic.security.jwt import create_access_token, verify_access_token

# ------------------------------------------------------------------

# create_access_token: payloadを署名してJWT文字列を生成する
# verify_access_token: 署名を検証してpayloadを復元する。不正なトークンの場合は例外を送出する


# 正常系のテスト（生成したトークンをそのまま検証できる）
def test_create_and_verify_access_token_success() -> None:
    # create_access_tokenで生成したトークンをverify_access_tokenに渡すと、
    # 渡したpayloadの内容がそのまま復元できることを確認する
    payload = {"sub": "1", "role": "employee"}

    token = create_access_token(payload)
    result = verify_access_token(token)

    assert result["sub"] == "1"
    assert result["role"] == "employee"


# ------------------------


# 正常系のテスト（有効期限(exp)が正しく設定される）
@freeze_time("2026-05-01 12:00:00+00:00")
def test_create_access_token_sets_expiration() -> None:
    # exp（有効期限）が「現在時刻 + jwt_expire_minutes」の値で設定されていることを確認する
    token = create_access_token({"sub": "1"})

    payload = verify_access_token(token)

    expected_exp = int(datetime(2026, 5, 1, 12, 0, 0, tzinfo=UTC).timestamp())
    expected_exp += core_settings.jwt_expire_minutes * 60
    assert payload["exp"] == expected_exp


# ------------------------


# 異常系のテスト（有効期限切れ）
def test_verify_access_token_raises_when_expired() -> None:
    # 有効期限切れのトークンを検証すると、jwt.ExpiredSignatureErrorが送出されることを確認する
    with freeze_time("2026-05-01 12:00:00+00:00") as frozen_time:
        token = create_access_token({"sub": "1"})
        frozen_time.tick(delta=timedelta(minutes=core_settings.jwt_expire_minutes + 1))

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

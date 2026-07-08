import pytest

from helpdesk_be.logic.validate.validate_password import validate_password


def test_validate_password_success() -> None:
    # 文字数・数字・大文字の条件をすべて満たす正常系で、値がそのまま返ることを確認する
    password = "Password1"

    result = validate_password(password)

    assert result == password


# ---------------------------------------------------------------------------------------


def test_validate_password_success_with_minimum_length() -> None:
    # 「8文字未満はNG」という境界条件の実装ミス（< と <= の取り違え等）を検知するため、
    # ちょうど8文字のケースが弾かれずに通過することを確認する
    password = "Passwor1"

    result = validate_password(password)

    assert result == password


# ---------------------------------------------------------------------------------------


def test_validate_password_raises_when_too_short() -> None:
    # 8文字未満の入力を弾くルールが機能していることを確認する
    with pytest.raises(ValueError, match="パスワードは8文字以上で入力してください"):
        validate_password("Pass1")


def test_validate_password_raises_when_no_digit() -> None:
    # 数字を1文字も含まない入力を弾くルールが機能していることを確認する
    with pytest.raises(ValueError, match="パスワードには数字を1文字以上含めてください"):
        validate_password("Password")


def test_validate_password_raises_when_no_uppercase() -> None:
    # 大文字を1文字も含まない入力を弾くルールが機能していることを確認する
    with pytest.raises(ValueError, match="パスワードには大文字を1文字以上含めてください"):
        validate_password("password1")

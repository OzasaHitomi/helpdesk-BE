from helpdesk_be.logic.security.password import hash_password, verify_password

# ------------------------------------------------------------------

# hash_password: 平文パスワードをbcryptでハッシュ化する
# verify_password: 平文パスワードとハッシュ値を照合する


# 正常系のテスト（ハッシュ化した値は平文と異なる文字列になる）
def test_hash_password_returns_different_string_from_plain() -> None:
    # ハッシュ化された値がそのまま平文として保存されていないことを確認する
    plain_password = "Password1"

    hashed = hash_password(plain_password)

    assert hashed != plain_password


# ------------------------


# 正常系のテスト（同じ平文でもソルトにより毎回異なるハッシュ値になる）
def test_hash_password_returns_different_hash_each_time() -> None:
    # gensalt()によりランダムなソルトが使われるため、同じ平文でも毎回異なるハッシュ値になることを確認する
    plain_password = "Password1"

    hashed1 = hash_password(plain_password)
    hashed2 = hash_password(plain_password)

    assert hashed1 != hashed2


# ------------------------


# 正常系のテスト（正しい平文とハッシュ値の組み合わせはTrueになる）
def test_verify_password_returns_true_when_matching() -> None:
    plain_password = "Password1"
    hashed = hash_password(plain_password)

    result = verify_password(plain_password, hashed)

    assert result is True


# ------------------------


# 準正常系のテスト（誤った平文とハッシュ値の組み合わせはFalseになる）
def test_verify_password_returns_false_when_not_matching() -> None:
    hashed = hash_password("Password1")

    result = verify_password("WrongPassword1", hashed)

    assert result is False

from helpdesk_be.exceptions.unauthorized_exception import UnauthorizedException

# ------------------------------------------------------------------

# UnauthorizedException: raise時にstatus_codeが401固定で設定される例外


# 正常系のテスト（メッセージ未指定時はデフォルトメッセージが設定される）
def test_unauthorized_exception_uses_default_message() -> None:
    exception = UnauthorizedException()

    assert exception.status_code == 401
    assert exception.detail == "認証に失敗しました"


# ------------------------


# 正常系のテスト（メッセージを指定した場合はそのメッセージが設定される）
def test_unauthorized_exception_uses_specified_message() -> None:
    exception = UnauthorizedException("カスタムメッセージ")

    assert exception.status_code == 401
    assert exception.detail == "カスタムメッセージ"

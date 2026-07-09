from helpdesk_be.exceptions.forbidden_exception import ForbiddenException

# ------------------------------------------------------------------

# ForbiddenException: raise時にstatus_codeが403固定で設定される例外


# 正常系のテスト（メッセージ未指定時はデフォルトメッセージが設定される）
def test_forbidden_exception_uses_default_message() -> None:
    exception = ForbiddenException()

    assert exception.status_code == 403
    assert exception.detail == "この操作は許可されていません"


# ------------------------


# 正常系のテスト（メッセージを指定した場合はそのメッセージが設定される）
def test_forbidden_exception_uses_specified_message() -> None:
    exception = ForbiddenException("カスタムメッセージ")

    assert exception.status_code == 403
    assert exception.detail == "カスタムメッセージ"

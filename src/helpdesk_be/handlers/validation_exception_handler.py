from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from helpdesk_be.logic.business.ticket import BLANK_MESSAGE

# 項目自体が未送信(missing)、または空文字列(string_too_short)の場合は、
# not_blankの対象外(空白のみの入力ではない)だが、利用者から見れば「空欄のまま送った」のと同じなので
# not_blankと同じメッセージにそろえる
BLANK_ERROR_TYPES = {"missing", "string_too_short"}

# 上記以外の、想定外のバリデーションエラー用の代わりの文言
DEFAULT_MESSAGE = "入力内容が正しくありません"


# FastAPIは422(バリデーションエラー)発生時、自作のメッセージを
# detailが配列になった独自形式で返してしまい、フロントがそのまま表示できない。
# そのため、その中から自分たちのメッセージだけを取り出し、
# {"detail": "メッセージ"}というシンプルな形に直して返す。
def handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    errors = exc.errors()
    message = DEFAULT_MESSAGE

    if errors:
        first_error = errors[0]
        # ctx["error"]に自作バリデーションのメッセージが入っているが、
        # 文字列ではなくValueErrorインスタンスなのでstr()で文字列に変換する
        error = first_error.get("ctx", {}).get("error")
        if error is not None:
            message = str(error)
        elif first_error.get("type") in BLANK_ERROR_TYPES:
            message = BLANK_MESSAGE

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": message},
    )

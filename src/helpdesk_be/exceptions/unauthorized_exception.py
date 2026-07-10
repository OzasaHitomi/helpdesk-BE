from fastapi import HTTPException, status


# 401 Unauthorized（認証情報が不正・未認証）を表すビジネス例外
# raise時にメッセージのみ渡せば、ステータスコードは自動で401になる
class UnauthorizedException(HTTPException):
    def __init__(self, msg: str | None = "認証に失敗しました") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=msg)

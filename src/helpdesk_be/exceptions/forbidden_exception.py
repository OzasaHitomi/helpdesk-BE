from fastapi import HTTPException, status


# 403 Forbidden（対象は認識できているが権限的に処理できない）を表すビジネス例外
# raise時にメッセージのみ渡せば、ステータスコードは自動で403になる
class ForbiddenException(HTTPException):
    def __init__(self, msg: str | None = "この操作は許可されていません") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=msg)

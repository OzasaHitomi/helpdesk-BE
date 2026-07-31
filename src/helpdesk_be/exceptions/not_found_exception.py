from fastapi import HTTPException, status


# 404 Not Found（対象のリソースが存在しない、または存在の有無を推測させたくない）を表すビジネス例外
# raise時にメッセージのみ渡せば、ステータスコードは自動で404になる
class NotFoundException(HTTPException):
    def __init__(self, msg: str | None = "対象のデータが見つかりません") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=msg)

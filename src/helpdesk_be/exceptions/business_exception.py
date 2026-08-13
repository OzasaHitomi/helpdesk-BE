from fastapi import HTTPException, status


# 422 Unprocessable Content（リクエスト自体は正しいが、リソースの現在の状態と矛盾するため処理できない）を表すビジネス例外
# raise時にメッセージのみ渡せば、ステータスコードは自動で422になる
class BusinessException(HTTPException):
    def __init__(self, msg: str | None = "処理できないリクエストです") -> None:
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=msg)

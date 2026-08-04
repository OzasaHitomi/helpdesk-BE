from datetime import datetime

from helpdesk_be.schemas.response.v1.base import BaseV1ResponseSchema

# フィールドの並びはmodels(TicketComment)の定義順に合わせる


# 対応履歴一覧APIの1件分のレスポンス。投稿者は先読みで取得した名前のみを返す
# (画面要件は対応日・担当者・対応内容の3つだが、FEがリスト描画のkeyに使えるようidも返す)
class GetTicketCommentsResponseItem(BaseV1ResponseSchema):
    id: int
    content: str
    commenter_name: str
    created_at: datetime

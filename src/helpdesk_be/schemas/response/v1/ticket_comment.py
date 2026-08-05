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


# チケット対応履歴(質問・返信)投稿APIのレスポンス。
# create系はcreated_at/updated_atを含めない方針(CreateTicketResponse)だが、
# コメント投稿は開いている対応履歴にその場で1件追記するUIを想定しているため、
# 追記表示に必要なcreated_at(サーバー時刻が正)を例外的に含める
class CreateTicketCommentResponse(BaseV1ResponseSchema):
    id: int
    ticket_id: int
    content: str
    created_by_user_id: int
    created_at: datetime

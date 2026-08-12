from datetime import datetime

from helpdesk_be.schemas.response.v1.base import BaseV1ResponseSchema
from helpdesk_be.store.enum.ticket_status_type import TicketStatusType
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType

# フィールドの並びはmodels(Ticket)の定義順に合わせる


# チケット新規作成APIのレスポンス。create系はcreated_at/updated_at以外は
# フォームで入力・決定された内容として返却する方針
class CreateTicketResponse(BaseV1ResponseSchema):
    id: int
    title: str
    detail: str
    visibility: TicketVisibilityType
    status: TicketStatusType
    created_by_user_id: int
    # 作成時点では未担当のためNone
    support_user_id: int | None


# チケット一覧APIの1件分のレスポンス。質問者・担当者は先読みで取得した名前のみを返す
class GetTicketsResponseItem(BaseV1ResponseSchema):
    id: int
    title: str
    visibility: TicketVisibilityType
    status: TicketStatusType
    questioner_name: str
    # 担当者が未割当ての場合はNone
    support_user_name: str | None
    created_at: datetime


# チケット詳細APIのレスポンス。担当者未割当ての場合はsupport_user_nameはNone
class GetTicketResponse(BaseV1ResponseSchema):
    id: int
    title: str
    detail: str
    visibility: TicketVisibilityType
    status: TicketStatusType
    support_user_id: int | None
    support_user_name: str | None
    created_at: datetime


# チケット担当者の自己アサインAPIのレスポンス
class AssignTicketResponse(BaseV1ResponseSchema):
    id: int
    status: TicketStatusType
    support_user_id: int
    support_user_name: str
    updated_at: datetime

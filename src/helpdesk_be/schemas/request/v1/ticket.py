from typing import Annotated

from pydantic import Field, StringConstraints

from helpdesk_be.schemas.request.v1.base import BaseV1RequestSchema
from helpdesk_be.store.enum.ticket_status_type import TicketStatusType
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType

# 前後の空白を除去した上でmin_lengthを判定する(空白のみの入力は未入力とみなしてNGにするため)
NotBlankStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


# チケット新規作成APIのリクエストボディを表すスキーマ
class CreateTicketRequest(BaseV1RequestSchema):
    # ticketsテーブルのtitle(String(255))に合わせた要件(タイトル)
    title: NotBlankStr = Field(max_length=255)
    # ticketsテーブルのdetail(Text)に合わせた詳細
    detail: NotBlankStr
    # 省略を許容しない(必ず利用者に公開設定を選択させる運用のため)
    visibility: TicketVisibilityType


# チケットステータス変更APIのリクエストボディを表すスキーマ
class UpdateTicketStatusRequest(BaseV1RequestSchema):
    status: TicketStatusType

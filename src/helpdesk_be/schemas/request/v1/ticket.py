from pydantic import Field, field_validator

from helpdesk_be.logic.business.ticket import not_blank
from helpdesk_be.schemas.request.v1.base import BaseV1RequestSchema
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType


# チケット新規作成APIのリクエストボディを表すスキーマ
class CreateTicketRequest(BaseV1RequestSchema):
    # ticketsテーブルのtitle(String(255))に合わせた要件(タイトル)
    title: str = Field(min_length=1, max_length=255)
    # ticketsテーブルのdetail(Text)に合わせた詳細
    detail: str = Field(min_length=1)
    # 指定が無い場合はデフォルトで非公開として扱う
    visibility: TicketVisibilityType = TicketVisibilityType.PRIVATE

    _validate_title = field_validator("title")(not_blank)
    _validate_detail = field_validator("detail")(not_blank)

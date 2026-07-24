from sqlalchemy.orm import Session

from helpdesk_be.models.ticket import Ticket
from helpdesk_be.store.enum.ticket_status_type import TicketStatusType
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType


# 位置引数ではなくキーワード引数
# created_by_user_idはticketsテーブルの外部キーのため、既定値を持たせず必ず呼び出し側から渡す
def create_ticket(db_session: Session, **update_data: object) -> Ticket:
    data = {
        "title": "test title",
        "detail": "test detail",
        "visibility": TicketVisibilityType.PRIVATE,
        "status": TicketStatusType.NEW_QUESTION,
    }
    data.update(**update_data)

    ticket_data = Ticket(**data)
    db_session.add(ticket_data)
    db_session.commit()
    return ticket_data

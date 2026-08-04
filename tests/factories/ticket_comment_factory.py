from sqlalchemy.orm import Session

from helpdesk_be.models.ticket_comment import TicketComment


# 位置引数ではなくキーワード引数
# ticket_idはticket_commentsテーブルの外部キーのため、既定値を持たせず必ず呼び出し側から渡す
# created_by_user_idはユーザー投稿の場合は呼び出し側から渡し、システム履歴の場合は渡さない(NULLになる)
def create_ticket_comment(db_session: Session, **update_data: object) -> TicketComment:
    data: dict[str, object] = {
        "content": "test content",
    }
    data.update(**update_data)

    comment_data = TicketComment(**data)
    db_session.add(comment_data)
    db_session.commit()
    return comment_data

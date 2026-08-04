from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from helpdesk_be.models.ticket_comment import TicketComment


# 指定チケットの対応履歴(質疑応答)一覧を投稿日時の降順(新しいものが先頭)で取得する
def get_comments_with_users_by_ticket_id(session: Session, ticket_id: int) -> list[TicketComment]:
    query = (
        select(TicketComment)
        # commenterを先読みし、後続のcomment.commenter.nameでのN+1クエリを防ぐ
        .options(selectinload(TicketComment.commenter))
        .where(TicketComment.ticket_id == ticket_id)
        # 同時刻のレコードが並んでもテストが安定するようidでタイブレークする
        .order_by(TicketComment.created_at.desc(), TicketComment.id.desc())
    )
    return list(session.execute(query).scalars().all())

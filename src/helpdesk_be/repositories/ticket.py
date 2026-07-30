from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from helpdesk_be.models.ticket import Ticket
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType


# 質問者・担当者情報を読み込んだチケット一覧を質問日(created_at)の降順で取得する(担当者未割当の場合はNone)
# visible_to_user_id: このユーザーidから閲覧可能なチケットのみに絞り込む。全件閲覧可能なロール(SUPPORT/ADMIN)の場合は
#                     呼び出し元がNoneを渡す想定で、その場合は絞り込みを行わず全件返す
def get_tickets_with_users(session: Session, visible_to_user_id: int | None = None) -> list[Ticket]:
    query = (
        select(Ticket)
        # questioner/support_userを先読みし、後続のticket.questioner.name等でのN+1クエリを防ぐ
        .options(selectinload(Ticket.questioner), selectinload(Ticket.support_user))
        # 質問日が新しい順。同時刻のレコードが並んでもテストが安定するようidでタイブレークする
        .order_by(Ticket.created_at.desc(), Ticket.id.desc())
    )

    if visible_to_user_id is not None:
        # 絞り込みが必要な場合(全件閲覧不可のロール)のみ、公開チケットまたは本人が質問者のチケットに絞り込む
        query = query.where(
            or_(
                Ticket.visibility == TicketVisibilityType.PUBLIC,
                Ticket.created_by_user_id == visible_to_user_id,
            )
        )

    return list(session.execute(query).scalars().all())

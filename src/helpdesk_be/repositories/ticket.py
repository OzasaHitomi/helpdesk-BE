from sqlalchemy import or_, select
from sqlalchemy.orm import Session, aliased

from helpdesk_be.models.ticket import Ticket
from helpdesk_be.models.user import User
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType


# 質問者・担当者情報を結合したチケット一覧を質問日(created_at)の降順で全件取得する(担当者未割当の場合はNone)
def get_tickets_all(session: Session) -> list[tuple[Ticket, User, User | None]]:
    # created_by_user_id/support_user_idはどちらもusers.idを参照するFKのため、別名を分けてJOINする
    questioner = aliased(User)
    support_user = aliased(User)

    query = (
        select(Ticket, questioner, support_user)
        .join(questioner, Ticket.created_by_user_id == questioner.id)
        # INNER JOINだと担当者未割当のチケットが結果から除外されてしまうため、LEFT JOINにしてsupport_user側がNoneでも行を残す
        .outerjoin(support_user, Ticket.support_user_id == support_user.id)
        # 質問日が新しい順。同時刻のレコードが並んでもテストが安定するようidでタイブレークする
        .order_by(Ticket.created_at.desc(), Ticket.id.desc())
    )

    return list(session.execute(query).tuples().all())


# ------------------------------------------------------------------------------------------------------------------------------------------------------


# 質問者・担当者情報を結合したチケット一覧のうち、「公開」または「本人が質問者」のものだけを質問日(created_at)の降順で取得する(担当者未割当の場合はNone)
def get_tickets_visible_to(
    session: Session, user_id: int
) -> list[tuple[Ticket, User, User | None]]:
    questioner = aliased(User)
    support_user = aliased(User)

    query = (
        select(Ticket, questioner, support_user)
        .join(questioner, Ticket.created_by_user_id == questioner.id)
        .outerjoin(support_user, Ticket.support_user_id == support_user.id)
        .where(
            or_(
                Ticket.visibility == TicketVisibilityType.PUBLIC,
                Ticket.created_by_user_id == user_id,
            )
        )
        .order_by(Ticket.created_at.desc(), Ticket.id.desc())
    )

    return list(session.execute(query).tuples().all())

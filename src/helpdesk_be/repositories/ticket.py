from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from helpdesk_be.models.ticket import Ticket
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType


# 質問者・担当者情報を読み込んだチケット一覧を質問日(created_at)の降順で取得する(担当者未割当の場合はNone)
# visible_to_user_id: このユーザーidから閲覧可能なチケットのみに絞り込む。全件閲覧可能なロール(SUPPORT/ADMIN)の場合は
#                     呼び出し元がNoneを渡す想定で、その場合は絞り込みを行わず全件返す
# この絞り込み条件はlogic/business/ticket_permission.pyのcan_view_ticketと同一ルールである
# (一覧はパフォーマンスのためSQLで絞り込み、詳細は1件のみのためPython側の関数で判定している)。
# 閲覧可否ルールを変更する場合は両方修正すること
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


# idを指定してチケット1件を取得する(存在しない場合はNone)。idはtickets.idの主キーのため一意性が保証されている
def get_ticket_by_id(session: Session, ticket_id: int) -> Ticket | None:
    query = select(Ticket).where(Ticket.id == ticket_id)
    return session.execute(query).scalar_one_or_none()

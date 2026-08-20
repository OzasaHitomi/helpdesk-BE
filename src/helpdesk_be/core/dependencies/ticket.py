from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.auth import get_current_user
from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.exceptions.not_found_exception import NotFoundException
from helpdesk_be.logic.business.ticket_permission import can_view_ticket
from helpdesk_be.models.ticket import Ticket
from helpdesk_be.models.user import User
from helpdesk_be.repositories.ticket import get_ticket_by_id
from helpdesk_be.store.enum.user_role_type import UserRoleType


# ticket_idのチケットを取得する。存在しない場合は404を送出する(チケット系APIで共通の存在チェック)
def get_ticket_or_404(
    ticket_id: int,
    session: Annotated[Session, Depends(get_db)],
) -> Ticket:
    ticket = get_ticket_by_id(session, ticket_id)
    if ticket is None:
        raise NotFoundException("チケットが見つかりません")
    return ticket


# 閲覧権限チェック: can_view_ticketで閲覧不可と判定された場合、存在有無を推測させないよう404で統一する(fail-closed)
def require_viewable_ticket(
    ticket: Annotated[Ticket, Depends(get_ticket_or_404)],
    user: Annotated[User, Depends(get_current_user)],
) -> Ticket:
    if not can_view_ticket(user, ticket):
        raise NotFoundException("チケットが見つかりません")
    return ticket


# 担当解除権限チェック: 自分が担当しているチケットのみ操作可能。
# support_user_idはSUPPORTロールのユーザーしかセットされない(assign_ticket_to_self参照)ため、
# この1チェックでロール違い・未担当・別担当者のケースを全てカバーできる
def require_own_assigned_ticket(
    ticket: Annotated[Ticket, Depends(get_ticket_or_404)],
    user: Annotated[User, Depends(get_current_user)],
) -> Ticket:
    if ticket.support_user_id != user.id:
        raise ForbiddenException("自分が担当しているチケットのみ担当解除できます")
    return ticket


# ステータス変更権限チェック: 自分が担当しているチケットのSUPPORT、またはADMINのみ変更可能。
# support_user_idはSUPPORTロールのユーザーしかセットされない(assign_ticket_to_self参照)ため、
# ADMIN以外はsupport_user_id != user.idの1チェックでロール違い・非担当をカバーできる
def require_ticket_status_editable(
    ticket: Annotated[Ticket, Depends(get_ticket_or_404)],
    user: Annotated[User, Depends(get_current_user)],
) -> Ticket:
    if user.role != UserRoleType.ADMIN and ticket.support_user_id != user.id:
        raise ForbiddenException("担当者または管理者のみステータスを変更できます")
    return ticket

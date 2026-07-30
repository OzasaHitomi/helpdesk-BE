from helpdesk_be.models.ticket import Ticket
from helpdesk_be.models.user import User
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType
from helpdesk_be.store.enum.user_role_type import UserRoleType


# ユーザーが指定のチケットを閲覧可能かどうかを判定する(SUPPORT/ADMINは全件、それ以外は公開チケットまたは自分が質問者のチケットのみ)
# repositories/ticket.pyのget_tickets_with_usersにおける絞り込み条件と同一ルールのため、
# ルールを変更する場合は両方修正すること
def can_view_ticket(user: User, ticket: Ticket) -> bool:
    if user.role in (UserRoleType.SUPPORT, UserRoleType.ADMIN):
        return True
    return ticket.visibility == TicketVisibilityType.PUBLIC or ticket.created_by_user_id == user.id

from helpdesk_be.logic.business.ticket_permission import can_view_ticket
from helpdesk_be.models.ticket import Ticket
from helpdesk_be.models.user import User
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType
from helpdesk_be.store.enum.user_role_type import UserRoleType


def _user(role: UserRoleType, user_id: int = 1) -> User:
    return User(
        id=user_id, name="テストユーザー", email="test@example.com", password_hash="hash", role=role
    )


def _ticket(created_by_user_id: int, visibility: TicketVisibilityType) -> Ticket:
    return Ticket(
        title="タイトル",
        detail="詳細",
        visibility=visibility,
        created_by_user_id=created_by_user_id,
    )


# 社員は公開チケットを閲覧できる
def test_can_view_ticket_returns_true_for_employee_and_public_ticket() -> None:
    user = _user(UserRoleType.EMPLOYEE, user_id=1)
    ticket = _ticket(created_by_user_id=2, visibility=TicketVisibilityType.PUBLIC)

    assert can_view_ticket(user, ticket) is True


# ---------------------------------------------------------------------------------------


# 社員は自分が質問者の非公開チケットを閲覧できる
def test_can_view_ticket_returns_true_for_employee_and_own_private_ticket() -> None:
    user = _user(UserRoleType.EMPLOYEE, user_id=1)
    ticket = _ticket(created_by_user_id=1, visibility=TicketVisibilityType.PRIVATE)

    assert can_view_ticket(user, ticket) is True


# ---------------------------------------------------------------------------------------


# 社員は他人が質問者の非公開チケットを閲覧できない
def test_can_view_ticket_returns_false_for_employee_and_others_private_ticket() -> None:
    user = _user(UserRoleType.EMPLOYEE, user_id=1)
    ticket = _ticket(created_by_user_id=2, visibility=TicketVisibilityType.PRIVATE)

    assert can_view_ticket(user, ticket) is False


# ---------------------------------------------------------------------------------------


# サポートロールは他人が質問者の非公開チケットも閲覧できる
def test_can_view_ticket_returns_true_for_support_and_others_private_ticket() -> None:
    user = _user(UserRoleType.SUPPORT, user_id=1)
    ticket = _ticket(created_by_user_id=2, visibility=TicketVisibilityType.PRIVATE)

    assert can_view_ticket(user, ticket) is True


# ---------------------------------------------------------------------------------------


# 管理者ロールも他人が質問者の非公開チケットを閲覧できる
def test_can_view_ticket_returns_true_for_admin_and_others_private_ticket() -> None:
    user = _user(UserRoleType.ADMIN, user_id=1)
    ticket = _ticket(created_by_user_id=2, visibility=TicketVisibilityType.PRIVATE)

    assert can_view_ticket(user, ticket) is True

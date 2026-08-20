import pytest

from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.ticket import (
    get_ticket_or_404,
    require_own_assigned_ticket,
    require_ticket_status_editable,
    require_viewable_ticket,
)
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.exceptions.not_found_exception import NotFoundException
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType
from helpdesk_be.store.enum.user_role_type import UserRoleType
from tests.factories.ticket_factory import create_ticket
from tests.factories.user_factory import create_user

# ------------------------------------------------------------------

# get_ticket_or_404: ticket_idのチケットを取得する。存在しない場合は404を送出する


# 正常系のテスト(存在するticket_idを渡すとそのチケットが取得できる)
def test_get_ticket_or_404_returns_ticket_when_exists(db_session: Session) -> None:
    questioner = create_user(db_session, email="questioner@example.com", role=UserRoleType.EMPLOYEE)
    ticket = create_ticket(db_session, created_by_user_id=questioner.id)

    result = get_ticket_or_404(ticket_id=ticket.id, session=db_session)

    assert result.id == ticket.id


# ------------------------


# 異常系のテスト(存在しないticket_idの場合は404)
def test_get_ticket_or_404_raises_not_found_when_ticket_does_not_exist(
    db_session: Session,
) -> None:
    with pytest.raises(NotFoundException) as exc_info:
        get_ticket_or_404(ticket_id=999, session=db_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "チケットが見つかりません"


# ====================================================================
# require_viewable_ticket
# ====================================================================


# 正常系のテスト(公開チケットは質問者以外(社員)でも閲覧可能)
def test_require_viewable_ticket_returns_ticket_when_public(db_session: Session) -> None:
    questioner = create_user(db_session, email="questioner@example.com", role=UserRoleType.EMPLOYEE)
    other_employee = create_user(
        db_session, email="other_employee@example.com", role=UserRoleType.EMPLOYEE
    )
    ticket = create_ticket(
        db_session,
        created_by_user_id=questioner.id,
        visibility=TicketVisibilityType.PUBLIC,
    )

    result = require_viewable_ticket(ticket=ticket, user=other_employee)

    assert result.id == ticket.id


# ------------------------


# 異常系のテスト(非公開チケットを質問者以外(社員)が閲覧しようとした場合、存在有無を推測させないよう404)
def test_require_viewable_ticket_raises_not_found_when_private_and_not_questioner(
    db_session: Session,
) -> None:
    questioner = create_user(db_session, email="questioner@example.com", role=UserRoleType.EMPLOYEE)
    other_employee = create_user(
        db_session, email="other_employee@example.com", role=UserRoleType.EMPLOYEE
    )
    ticket = create_ticket(
        db_session,
        created_by_user_id=questioner.id,
        visibility=TicketVisibilityType.PRIVATE,
    )

    with pytest.raises(NotFoundException) as exc_info:
        require_viewable_ticket(ticket=ticket, user=other_employee)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "チケットが見つかりません"


# ====================================================================
# require_own_assigned_ticket
# ====================================================================


# 正常系のテスト(自分が担当しているチケットは操作可能)
def test_require_own_assigned_ticket_returns_ticket_when_own_assignee(
    db_session: Session,
) -> None:
    questioner = create_user(db_session, email="questioner@example.com", role=UserRoleType.EMPLOYEE)
    support_user = create_user(db_session, email="support@example.com", role=UserRoleType.SUPPORT)
    ticket = create_ticket(
        db_session, created_by_user_id=questioner.id, support_user_id=support_user.id
    )

    result = require_own_assigned_ticket(ticket=ticket, user=support_user)

    assert result.id == ticket.id


# ------------------------


# 異常系のテスト(自分が担当していないチケットは403)
def test_require_own_assigned_ticket_raises_forbidden_when_not_own_assignee(
    db_session: Session,
) -> None:
    questioner = create_user(db_session, email="questioner@example.com", role=UserRoleType.EMPLOYEE)
    assigned_support_user = create_user(
        db_session, email="assigned_support@example.com", role=UserRoleType.SUPPORT
    )
    other_support_user = create_user(
        db_session, email="other_support@example.com", role=UserRoleType.SUPPORT
    )
    ticket = create_ticket(
        db_session,
        created_by_user_id=questioner.id,
        support_user_id=assigned_support_user.id,
    )

    with pytest.raises(ForbiddenException) as exc_info:
        require_own_assigned_ticket(ticket=ticket, user=other_support_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "自分が担当しているチケットのみ担当解除できます"


# ====================================================================
# require_ticket_status_editable
# ====================================================================


# 正常系のテスト(自分が担当しているチケットのSUPPORTは変更可能)
def test_require_ticket_status_editable_returns_ticket_when_own_assignee(
    db_session: Session,
) -> None:
    questioner = create_user(db_session, email="questioner@example.com", role=UserRoleType.EMPLOYEE)
    support_user = create_user(db_session, email="support@example.com", role=UserRoleType.SUPPORT)
    ticket = create_ticket(
        db_session, created_by_user_id=questioner.id, support_user_id=support_user.id
    )

    result = require_ticket_status_editable(ticket=ticket, user=support_user)

    assert result.id == ticket.id


# ------------------------


# 正常系のテスト(担当の有無を問わずADMINは変更可能)
def test_require_ticket_status_editable_returns_ticket_when_admin(db_session: Session) -> None:
    questioner = create_user(db_session, email="questioner@example.com", role=UserRoleType.EMPLOYEE)
    support_user = create_user(db_session, email="support@example.com", role=UserRoleType.SUPPORT)
    admin_user = create_user(db_session, email="admin@example.com", role=UserRoleType.ADMIN)
    ticket = create_ticket(
        db_session, created_by_user_id=questioner.id, support_user_id=support_user.id
    )

    result = require_ticket_status_editable(ticket=ticket, user=admin_user)

    assert result.id == ticket.id


# ------------------------


# 異常系のテスト(担当外のSUPPORTは403)
def test_require_ticket_status_editable_raises_forbidden_when_not_own_assignee(
    db_session: Session,
) -> None:
    questioner = create_user(db_session, email="questioner@example.com", role=UserRoleType.EMPLOYEE)
    assigned_support_user = create_user(
        db_session, email="assigned_support@example.com", role=UserRoleType.SUPPORT
    )
    other_support_user = create_user(
        db_session, email="other_support@example.com", role=UserRoleType.SUPPORT
    )
    ticket = create_ticket(
        db_session,
        created_by_user_id=questioner.id,
        support_user_id=assigned_support_user.id,
    )

    with pytest.raises(ForbiddenException) as exc_info:
        require_ticket_status_editable(ticket=ticket, user=other_support_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "担当者または管理者のみステータスを変更できます"

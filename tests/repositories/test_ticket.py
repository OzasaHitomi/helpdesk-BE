from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from helpdesk_be.repositories.ticket import get_tickets_with_users
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType
from tests.factories.ticket_factory import create_ticket
from tests.factories.user_factory import create_user

# ====================================================================
# get_tickets_with_users (visible_to_user_id未指定 = 全件)
# ====================================================================


def test_get_tickets_with_users_returns_all_tickets_regardless_of_visibility_when_user_id_is_none(
    db_session: Session,
) -> None:
    # user_id未指定の場合、公開設定に関わらず全件返ることを確認する
    questioner = create_user(db_session)
    create_ticket(
        db_session, created_by_user_id=questioner.id, visibility=TicketVisibilityType.PUBLIC
    )
    create_ticket(
        db_session, created_by_user_id=questioner.id, visibility=TicketVisibilityType.PRIVATE
    )

    rows = get_tickets_with_users(db_session)

    assert len(rows) == 2


# ---------------------------------------------------------------------------------------


def test_get_tickets_with_users_orders_by_created_at_desc(db_session: Session) -> None:
    # 質問日(created_at)が新しい順に返ることを確認する
    questioner = create_user(db_session)
    old_ticket = create_ticket(
        db_session,
        created_by_user_id=questioner.id,
        created_at=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Tokyo")),
    )
    new_ticket = create_ticket(
        db_session,
        created_by_user_id=questioner.id,
        created_at=datetime(2026, 7, 1, tzinfo=ZoneInfo("Asia/Tokyo")),
    )

    rows = get_tickets_with_users(db_session)

    assert [ticket.id for ticket in rows] == [new_ticket.id, old_ticket.id]


# ---------------------------------------------------------------------------------------


def test_get_tickets_with_users_returns_empty_sequence_when_no_tickets_exist(
    db_session: Session,
) -> None:
    # チケットが1件も存在しない場合は空のシーケンスが返ることを確認する
    rows = get_tickets_with_users(db_session)

    assert rows == []


# ---------------------------------------------------------------------------------------


def test_get_tickets_with_users_returns_none_support_user_when_unassigned(
    db_session: Session,
) -> None:
    # 担当者が未割当て(support_user_id=None)の場合、support_userがNoneになることを確認する
    questioner = create_user(db_session)
    create_ticket(db_session, created_by_user_id=questioner.id)

    rows = get_tickets_with_users(db_session)

    assert rows[0].support_user is None


# ====================================================================
# get_tickets_with_users (visible_to_user_id指定 = 閲覧可能なもののみ)
# ====================================================================


def test_get_tickets_with_users_filters_private_tickets_of_other_users_when_user_id_given(
    db_session: Session,
) -> None:
    # 「公開」または「本人が質問者」以外の非公開チケットは除外されることを確認する
    me = create_user(db_session, name="自分", email="me@example.com")
    other = create_user(db_session, name="他人", email="other@example.com")

    own_private = create_ticket(
        db_session,
        created_by_user_id=me.id,
        visibility=TicketVisibilityType.PRIVATE,
        title="自分の非公開",
    )
    other_public = create_ticket(
        db_session,
        created_by_user_id=other.id,
        visibility=TicketVisibilityType.PUBLIC,
        title="他人の公開",
    )
    create_ticket(
        db_session,
        created_by_user_id=other.id,
        visibility=TicketVisibilityType.PRIVATE,
        title="他人の非公開",
    )

    rows = get_tickets_with_users(db_session, visible_to_user_id=me.id)

    ticket_ids = {ticket.id for ticket in rows}
    assert ticket_ids == {own_private.id, other_public.id}

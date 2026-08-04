from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from helpdesk_be.repositories.ticket_comment import get_comments_with_users_by_ticket_id
from tests.factories.ticket_comment_factory import create_ticket_comment
from tests.factories.ticket_factory import create_ticket
from tests.factories.user_factory import create_user

# ====================================================================
# get_comments_with_users_by_ticket_id
# ====================================================================


def test_get_comments_with_users_by_ticket_id_orders_by_created_at_desc(
    db_session: Session,
) -> None:
    # 投稿日時(created_at)が新しい順に返ることを確認する
    user = create_user(db_session)
    ticket = create_ticket(db_session, created_by_user_id=user.id)
    old_comment = create_ticket_comment(
        db_session,
        ticket_id=ticket.id,
        created_by_user_id=user.id,
        created_at=datetime(2026, 1, 1, tzinfo=ZoneInfo("Asia/Tokyo")),
    )
    new_comment = create_ticket_comment(
        db_session,
        ticket_id=ticket.id,
        created_by_user_id=user.id,
        created_at=datetime(2026, 7, 1, tzinfo=ZoneInfo("Asia/Tokyo")),
    )

    rows = get_comments_with_users_by_ticket_id(db_session, ticket.id)

    assert [comment.id for comment in rows] == [new_comment.id, old_comment.id]


# ---------------------------------------------------------------------------------------


def test_get_comments_with_users_by_ticket_id_filters_by_ticket_id(db_session: Session) -> None:
    # 指定したticket_idのコメントのみが返り、他チケットのコメントは混ざらないことを確認する
    user = create_user(db_session)
    target_ticket = create_ticket(db_session, created_by_user_id=user.id, title="対象チケット")
    other_ticket = create_ticket(db_session, created_by_user_id=user.id, title="対象外チケット")
    target_comment = create_ticket_comment(
        db_session, ticket_id=target_ticket.id, created_by_user_id=user.id
    )
    create_ticket_comment(db_session, ticket_id=other_ticket.id, created_by_user_id=user.id)

    rows = get_comments_with_users_by_ticket_id(db_session, target_ticket.id)

    assert [comment.id for comment in rows] == [target_comment.id]


# ---------------------------------------------------------------------------------------


def test_get_comments_with_users_by_ticket_id_returns_empty_list_when_no_comments_exist(
    db_session: Session,
) -> None:
    # コメントが1件も存在しない場合は空のリストが返ることを確認する
    user = create_user(db_session)
    ticket = create_ticket(db_session, created_by_user_id=user.id)

    rows = get_comments_with_users_by_ticket_id(db_session, ticket.id)

    assert rows == []


# ---------------------------------------------------------------------------------------


def test_get_comments_with_users_by_ticket_id_preloads_commenter(db_session: Session) -> None:
    # 投稿者(commenter)が先読みされ、コメントごとの投稿者名が取得できることを確認する
    commenter = create_user(db_session, name="投稿太郎", email="commenter@example.com")
    ticket = create_ticket(db_session, created_by_user_id=commenter.id)
    create_ticket_comment(db_session, ticket_id=ticket.id, created_by_user_id=commenter.id)

    rows = get_comments_with_users_by_ticket_id(db_session, ticket.id)

    row_commenter = rows[0].commenter
    assert row_commenter is not None
    assert row_commenter.name == commenter.name


# ---------------------------------------------------------------------------------------


def test_get_comments_with_users_by_ticket_id_returns_comment_without_commenter(
    db_session: Session,
) -> None:
    # システムが自動登録した履歴(created_by_user_id=NULL)も取得でき、commenterはNoneになることを確認する
    user = create_user(db_session)
    ticket = create_ticket(db_session, created_by_user_id=user.id)
    create_ticket_comment(db_session, ticket_id=ticket.id)

    rows = get_comments_with_users_by_ticket_id(db_session, ticket.id)

    assert len(rows) == 1
    assert rows[0].commenter is None

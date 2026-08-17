import pytest

from helpdesk_be.logic.business.ticket_status_transition import can_transition_ticket_status
from helpdesk_be.store.enum.ticket_status_type import TicketStatusType


# 新規質問からは担当者割当て済みへのみ遷移できる(担当者の自己アサイン)
def test_can_transition_ticket_status_returns_true_from_new_question_to_assigned() -> None:
    assert (
        can_transition_ticket_status(TicketStatusType.NEW_QUESTION, TicketStatusType.ASSIGNED)
        is True
    )


# ---------------------------------------------------------------------------------------


# 担当者アサイン済みからは新規質問(担当解除)/対応中/解決済み/クローズへ遷移できる
@pytest.mark.parametrize(
    "next_status",
    [
        TicketStatusType.NEW_QUESTION,
        TicketStatusType.IN_PROGRESS,
        TicketStatusType.RESOLVED,
        TicketStatusType.CLOSED,
    ],
    ids=lambda s: s.value,
)
def test_can_transition_ticket_status_returns_true_from_assigned(
    next_status: TicketStatusType,
) -> None:
    assert can_transition_ticket_status(TicketStatusType.ASSIGNED, next_status) is True


# ---------------------------------------------------------------------------------------


# 対応中からは新規質問(担当解除)/担当者アサイン済み(差し戻し)/解決済み/クローズへ遷移できる
@pytest.mark.parametrize(
    "next_status",
    [
        TicketStatusType.NEW_QUESTION,
        TicketStatusType.ASSIGNED,
        TicketStatusType.RESOLVED,
        TicketStatusType.CLOSED,
    ],
    ids=lambda s: s.value,
)
def test_can_transition_ticket_status_returns_true_from_in_progress(
    next_status: TicketStatusType,
) -> None:
    assert can_transition_ticket_status(TicketStatusType.IN_PROGRESS, next_status) is True


# ---------------------------------------------------------------------------------------


# 解決済みからは対応中(再オープン)/クローズへ遷移できる
@pytest.mark.parametrize(
    "next_status",
    [TicketStatusType.IN_PROGRESS, TicketStatusType.CLOSED],
    ids=lambda s: s.value,
)
def test_can_transition_ticket_status_returns_true_from_resolved(
    next_status: TicketStatusType,
) -> None:
    assert can_transition_ticket_status(TicketStatusType.RESOLVED, next_status) is True


# ---------------------------------------------------------------------------------------


# クローズからは対応中(再オープン)のみ遷移できる
def test_can_transition_ticket_status_returns_true_from_closed_to_in_progress() -> None:
    assert (
        can_transition_ticket_status(TicketStatusType.CLOSED, TicketStatusType.IN_PROGRESS) is True
    )


# ---------------------------------------------------------------------------------------


# 現在のステータスへの遷移(no-op)や、許可されていない遷移はFalseになる
@pytest.mark.parametrize(
    ("current", "next_status"),
    [
        (TicketStatusType.NEW_QUESTION, TicketStatusType.NEW_QUESTION),
        (TicketStatusType.NEW_QUESTION, TicketStatusType.IN_PROGRESS),
        (TicketStatusType.NEW_QUESTION, TicketStatusType.RESOLVED),
        (TicketStatusType.NEW_QUESTION, TicketStatusType.CLOSED),
        (TicketStatusType.ASSIGNED, TicketStatusType.ASSIGNED),
        (TicketStatusType.IN_PROGRESS, TicketStatusType.IN_PROGRESS),
        (TicketStatusType.RESOLVED, TicketStatusType.RESOLVED),
        (TicketStatusType.RESOLVED, TicketStatusType.ASSIGNED),
        (TicketStatusType.RESOLVED, TicketStatusType.NEW_QUESTION),
        (TicketStatusType.CLOSED, TicketStatusType.CLOSED),
        (TicketStatusType.CLOSED, TicketStatusType.ASSIGNED),
        (TicketStatusType.CLOSED, TicketStatusType.RESOLVED),
        (TicketStatusType.CLOSED, TicketStatusType.NEW_QUESTION),
    ],
    ids=lambda v: v.value if isinstance(v, TicketStatusType) else str(v),
)
def test_can_transition_ticket_status_returns_false_for_disallowed_transitions(
    current: TicketStatusType, next_status: TicketStatusType
) -> None:
    assert can_transition_ticket_status(current, next_status) is False

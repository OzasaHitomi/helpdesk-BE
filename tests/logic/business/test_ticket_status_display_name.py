import pytest

from helpdesk_be.logic.business.ticket_status_display_name import (
    TICKET_STATUS_DISPLAY_NAMES,
    get_ticket_status_display_name,
)
from helpdesk_be.store.enum.ticket_status_type import TicketStatusType


# 各ステータスに対応する日本語表示名が返る
@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (TicketStatusType.NEW_QUESTION, "新規質問"),
        (TicketStatusType.ASSIGNED, "担当者割当て済み"),
        (TicketStatusType.IN_PROGRESS, "対応中"),
        (TicketStatusType.RESOLVED, "解決済み"),
        (TicketStatusType.CLOSED, "クローズ"),
    ],
    ids=lambda v: v.value if isinstance(v, TicketStatusType) else str(v),
)
def test_get_ticket_status_display_name_returns_japanese_name(
    status: TicketStatusType, expected: str
) -> None:
    assert get_ticket_status_display_name(status) == expected


# ---------------------------------------------------------------------------------------


# TicketStatusTypeの全メンバー分の表示名が定義されている(定義漏れがあるとKeyErrorになる)
@pytest.mark.parametrize(
    "status",
    list(TicketStatusType),
    ids=lambda s: s.value,
)
def test_ticket_status_display_names_covers_all_statuses(status: TicketStatusType) -> None:
    assert status in TICKET_STATUS_DISPLAY_NAMES


# ---------------------------------------------------------------------------------------


# 表示名の定義が漏れているステータスを渡すとKeyErrorになる
def test_get_ticket_status_display_name_raises_key_error_when_definition_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # 現状は全ステータス定義済みでKeyErrorを起こせないため、定義漏れをテスト内だけで人工的に再現する
    monkeypatch.delitem(TICKET_STATUS_DISPLAY_NAMES, TicketStatusType.NEW_QUESTION)

    with pytest.raises(KeyError):
        get_ticket_status_display_name(TicketStatusType.NEW_QUESTION)

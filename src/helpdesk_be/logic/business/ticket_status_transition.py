from helpdesk_be.store.enum.ticket_status_type import TicketStatusType

# 各ステータスから直接遷移可能なステータスの一覧。
# NEW_QUESTIONへの遷移・NEW_QUESTIONからの遷移はこの表に含めない
# (担当者の割当て/解除はassign_ticket_to_self/unassign_ticketが専任で管理するため)
TICKET_STATUS_TRANSITIONS: dict[TicketStatusType, set[TicketStatusType]] = {
    # 新規質問からの遷移はこの表で管理しない(担当者割当て時にassign_ticket_to_selfがASSIGNEDへ遷移させる)
    TicketStatusType.NEW_QUESTION: set(),
    # 担当者割当て済みから遷移可能 -> 対応中、解決済み、クローズ
    TicketStatusType.ASSIGNED: {
        TicketStatusType.IN_PROGRESS,
        TicketStatusType.RESOLVED,
        TicketStatusType.CLOSED,
    },
    # 対応中から遷移可能 -> 担当者割当て済み(差し戻し)、解決済み、クローズ
    TicketStatusType.IN_PROGRESS: {
        TicketStatusType.ASSIGNED,
        TicketStatusType.RESOLVED,
        TicketStatusType.CLOSED,
    },
    # 解決済みから遷移可能 -> 対応中(再オープン)、クローズ
    TicketStatusType.RESOLVED: {
        TicketStatusType.IN_PROGRESS,
        TicketStatusType.CLOSED,
    },
    # クローズから遷移可能 -> 対応中(再オープン)
    TicketStatusType.CLOSED: {
        TicketStatusType.IN_PROGRESS,
    },
}


def can_transition_ticket_status(current: TicketStatusType, next_status: TicketStatusType) -> bool:
    return next_status in TICKET_STATUS_TRANSITIONS[current]

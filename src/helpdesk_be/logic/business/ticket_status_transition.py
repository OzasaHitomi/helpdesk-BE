from helpdesk_be.store.enum.ticket_status_type import TicketStatusType

# 各ステータスから直接遷移可能なステータスの一覧。
# チケットのステータスそのものが取り得る遷移を網羅する(どのAPIがどの遷移を扱うかはこのロジックの関心事ではない。
# 特定のAPIが一部の遷移を扱わない場合、それはそのAPI側で判断・制御すること)
TICKET_STATUS_TRANSITIONS: dict[TicketStatusType, set[TicketStatusType]] = {
    # 新規質問から遷移可能 -> 担当者割当て済み(担当者の自己アサイン)
    TicketStatusType.NEW_QUESTION: {
        TicketStatusType.ASSIGNED,
    },
    # 担当者割当て済みから遷移可能 -> 新規質問(担当解除)、対応中、解決済み、クローズ
    TicketStatusType.ASSIGNED: {
        TicketStatusType.NEW_QUESTION,
        TicketStatusType.IN_PROGRESS,
        TicketStatusType.RESOLVED,
        TicketStatusType.CLOSED,
    },
    # 対応中から遷移可能 -> 新規質問(担当解除)、担当者割当て済み(差し戻し)、解決済み、クローズ
    TicketStatusType.IN_PROGRESS: {
        TicketStatusType.NEW_QUESTION,
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

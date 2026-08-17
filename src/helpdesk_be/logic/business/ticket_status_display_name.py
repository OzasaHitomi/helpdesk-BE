from helpdesk_be.store.enum.ticket_status_type import TicketStatusType

# ステータスの日本語表示名。対応履歴のcontentに埋め込む文言などに使う。
# クライアントからの入力をそのまま信用すると、ログイン済みユーザーが
# 直接APIを叩いた際に任意の文字列を履歴に残せてしまうため、BE側で一元管理する
TICKET_STATUS_DISPLAY_NAMES: dict[TicketStatusType, str] = {
    TicketStatusType.NEW_QUESTION: "新規質問",
    TicketStatusType.ASSIGNED: "担当者割当て済み",
    TicketStatusType.IN_PROGRESS: "対応中",
    TicketStatusType.RESOLVED: "解決済み",
    TicketStatusType.CLOSED: "クローズ",
}


def get_ticket_status_display_name(status: TicketStatusType) -> str:
    return TICKET_STATUS_DISPLAY_NAMES[status]

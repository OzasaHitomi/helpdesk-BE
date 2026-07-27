from enum import Enum


class TicketStatusType(Enum):
    NEW_QUESTION = "new_question"  # 新規質問
    ASSIGNED = "assigned"  # 担当者割当て済み
    IN_PROGRESS = "in_progress"  # 対応中
    RESOLVED = "resolved"  # 解決済み
    CLOSED = "closed"  # クローズ

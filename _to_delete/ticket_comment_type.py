from enum import Enum


class TicketCommentType(Enum):
    USER = "user"  # 利用者・サポート担当が入力した質問・返信
    SYSTEM = "system"  # 担当者割り当て等でシステムが自動登録した対応履歴

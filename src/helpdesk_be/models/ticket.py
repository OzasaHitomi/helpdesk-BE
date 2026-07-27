from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from helpdesk_be.logic.calculate.calc_datetime import get_now
from helpdesk_be.models.base import Base
from helpdesk_be.store.enum.ticket_status_type import TicketStatusType
from helpdesk_be.store.enum.ticket_visibility_type import TicketVisibilityType


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 要件（タイトル）。VARCHAR型、最大255文字という取り決めに合わせた長さ
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    # 詳細。TEXT型、日本語で約16,000文字程度を上限として想定した取り決めに合わせて採用
    detail: Mapped[str] = mapped_column(Text, nullable=False)
    visibility: Mapped[TicketVisibilityType] = mapped_column(
        Enum(TicketVisibilityType), nullable=False, default=TicketVisibilityType.PRIVATE
    )
    status: Mapped[TicketStatusType] = mapped_column(
        Enum(TicketStatusType), nullable=False, default=TicketStatusType.NEW_QUESTION
    )
    # チケットを作成した社員。サポート担当が依頼者を特定できるよう保持する
    # index=Trueにより、作成者ごとのチケット一覧取得を高速化する
    created_by_user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, index=True
    )
    # チケットを担当するサポート担当。作成時点では未担当のためnullable
    # （担当設定・解除のAPIでセット/NULLに戻す）。created_by_user_idと同じ理由でindexを付与
    support_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=get_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=get_now, onupdate=get_now
    )

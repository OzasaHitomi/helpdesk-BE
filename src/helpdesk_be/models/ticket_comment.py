from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from helpdesk_be.logic.calculate.calc_datetime import get_now
from helpdesk_be.models.base import Base
from helpdesk_be.models.user import User
from helpdesk_be.store.enum.user_role_type import UserRoleType


# チケット詳細画面の対応履歴(質疑応答の質問・返信)1件を表すテーブル。
# 質問/返信の区別カラムは持たず、投稿者(created_by_user_id)が誰かで判別できるためシンプルな1テーブル構成とする。
# 担当者割り当て等でシステムが自動登録する履歴もこのテーブルで扱い、created_by_user_id=NULLで表す
class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 対象チケット。index=Trueにより、チケットごとの対応履歴一覧取得を高速化する
    ticket_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tickets.id"), nullable=False, index=True
    )
    # 対応内容。tickets.detailと同じくTEXT型(日本語で約16,000文字程度を上限として想定した取り決めに合わせて採用)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # 投稿者。閲覧可能なチケットには誰でも投稿できる仕様(別タスク)のため、質問者・サポート担当以外のユーザーも入り得る。
    # 担当者割り当て等でシステムが自動登録した履歴の場合はNULL(画面上の対応者は"system"と表示する)。
    # このテーブルでNULLが表す意味は「システム履歴」のみとし、別の意味でNULLを使う仕様変更を行う場合は
    # commenter_display_name()の"system"判定と合わせて見直すこと
    created_by_user_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    # 対応履歴で「担当者」(投稿者名)を表示するために使用する。チケット自体のsupport_userとは別概念
    # (support_userは現在の担当者を指し可変、こちらは各投稿を実際に書いた人で不変)。
    # システム履歴(created_by_user_id=NULL)の場合はNone
    commenter: Mapped[User | None] = relationship(User, foreign_keys=[created_by_user_id])
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=get_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=get_now, onupdate=get_now
    )

    # 対応履歴一覧での投稿者名の表示ルール。
    # 投稿者がいない行(created_by_user_id=NULL)は担当者割り当て等でシステムが自動登録した履歴のため"system"。
    # 投稿者がADMINの場合は個人名を出さず「管理者」と匿名化する
    # (実際の投稿者IDはcreated_by_user_idに保持されるためDB上では追跡可能)
    def commenter_display_name(self) -> str:
        if self.commenter is None:
            return "system"
        if self.commenter.role == UserRoleType.ADMIN:
            return "管理者"
        return self.commenter.name

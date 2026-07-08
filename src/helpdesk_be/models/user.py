from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from helpdesk_be.logic.calculate.calc_datetime import get_now
from helpdesk_be.models.base import Base
from helpdesk_be.store.enum.user_role_type import UserRoleType


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 255は氏名を格納するのに十分な長さとして採用している一般的な文字数
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # 255はRFC 5321で定められたメールアドレスの最大長(254文字)を格納できる長さ
    # index=Trueにより、ログイン時のメールアドレス検索を高速化するための一意インデックスを付与している
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    # 255はbcrypt等のハッシュ値(60文字程度)より十分に大きく、将来的なハッシュアルゴリズム変更にも対応できる長さ
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRoleType] = mapped_column(Enum(UserRoleType), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=get_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=get_now, onupdate=get_now
    )

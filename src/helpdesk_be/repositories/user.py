from sqlalchemy import select
from sqlalchemy.orm import Session

from helpdesk_be.models.user import User
from helpdesk_be.store.enum.user_role_type import UserRoleType


# メールアドレス一致でユーザーを1件取得する。存在しない場合はNoneを返す
def get_user_by_email(session: Session, email: str) -> User | None:
    return session.execute(select(User).where(User.email == email)).scalar_one_or_none()


# ユーザーIDでユーザーを1件取得する。存在しない場合はNoneを返す
# JWTのペイロード(sub)にはユーザーIDのみが入っているため、認証時のユーザー復元に使う
def get_user_by_id(session: Session, user_id: int) -> User | None:
    return session.execute(select(User).where(User.id == user_id)).scalar_one_or_none()


# 社員・サポート担当のみを一覧取得する(管理者は対象外。作成日時の降順。同時刻のレコードが並んでもテストが安定するようidでタイブレークする)
def get_employee_and_support_users(session: Session) -> list[User]:
    query = (
        select(User)
        .where(User.role.in_([UserRoleType.EMPLOYEE, UserRoleType.SUPPORT]))
        .order_by(User.created_at.desc(), User.id.desc())
    )
    return list(session.execute(query).scalars().all())

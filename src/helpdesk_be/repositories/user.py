from sqlalchemy import select
from sqlalchemy.orm import Session

from helpdesk_be.models.user import User


# メールアドレス一致でユーザーを1件取得する。存在しない場合はNoneを返す
def get_user_by_email(session: Session, email: str) -> User | None:
    return session.execute(select(User).where(User.email == email)).scalar_one_or_none()

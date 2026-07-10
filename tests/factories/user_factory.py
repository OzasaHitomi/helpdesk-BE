from sqlalchemy.orm import Session

from helpdesk_be.models.user import User
from helpdesk_be.store.enum.user_role_type import UserRoleType


# 位置引数ではなくキーワード引数
def create_user(db_session: Session, **update_data: object) -> User:
    data = {
        "name": "test",
        "email": "test@example.com",
        "password_hash": "test_password_hash",
        "role": UserRoleType.EMPLOYEE,
        "is_active": True,
    }
    data.update(**update_data)

    # **辞書名→展開
    # アップデートしたデータ内容をUserの型に入れる
    user_data = User(**data)
    db_session.add(user_data)
    db_session.commit()
    return user_data

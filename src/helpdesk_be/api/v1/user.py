from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.auth import get_current_user
from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.models.user import User
from helpdesk_be.repositories.user import get_employee_and_support_users
from helpdesk_be.schemas.response.v1.user import GetUsersResponseItem
from helpdesk_be.store.enum.user_role_type import UserRoleType

router = APIRouter()


@router.get("", response_model=list[GetUsersResponseItem])
def list_users(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[GetUsersResponseItem]:
    # アカウント一覧の閲覧は管理者のみ許可する
    if user.role != UserRoleType.ADMIN:
        raise ForbiddenException("管理者のみこの操作を実行できます")

    # 社員・サポートアカウントのみを一覧表示対象とする(管理者は表示対象外)
    users = get_employee_and_support_users(session)

    return [
        GetUsersResponseItem(
            id=u.id,
            name=u.name,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
        )
        for u in users
    ]

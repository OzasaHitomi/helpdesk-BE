from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.core.dependencies.permission import require_role
from helpdesk_be.repositories.user import get_employee_and_support_users
from helpdesk_be.schemas.response.v1.user import GetUsersResponseItem
from helpdesk_be.store.enum.user_role_type import UserRoleType

router = APIRouter()


@router.get(
    "",
    response_model=list[GetUsersResponseItem],
    dependencies=[
        Depends(require_role({UserRoleType.ADMIN}, message="管理者のみこの操作を実行できます"))
    ],
)
def list_users(
    session: Annotated[Session, Depends(get_db)],
) -> list[GetUsersResponseItem]:
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

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.core.dependencies.permission import require_role
from helpdesk_be.exceptions.business_exception import BusinessException
from helpdesk_be.loggers.custom_logger import logger
from helpdesk_be.logic.security.password import hash_password
from helpdesk_be.models.user import User
from helpdesk_be.repositories.user import get_employee_and_support_users, get_user_by_email
from helpdesk_be.schemas.request.v1.user import CreateUserRequest
from helpdesk_be.schemas.response.v1.user import CreateUserResponse, GetUsersResponseItem
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


# ------------------------


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateUserResponse,
    dependencies=[
        Depends(require_role({UserRoleType.ADMIN}, message="管理者のみこの操作を実行できます"))
    ],
)
def create_user(
    body: CreateUserRequest,
    session: Annotated[Session, Depends(get_db)],
) -> CreateUserResponse:
    # --- 入力チェック: このAPIで発行できるアカウントタイプは社員・サポート担当者のみ ---
    if body.role == UserRoleType.ADMIN:
        raise BusinessException("アカウントタイプは社員またはサポート担当者のみ指定できます")

    # --- 重複チェック: 既に同じメールアドレスのアカウントが存在する場合は422 ---
    if get_user_by_email(session, body.email) is not None:
        raise BusinessException("このメールアドレスは既に登録されています")

    # --- 作成処理: パスワードはハッシュ化してから保存し、平文は保存しない ---
    new_user = User(
        name=body.name,
        email=body.email,
        password_hash=hash_password(body.password),
        role=body.role,
    )
    session.add(new_user)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"failed to create user {e}")
        raise e

    return CreateUserResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
        is_active=new_user.is_active,
    )

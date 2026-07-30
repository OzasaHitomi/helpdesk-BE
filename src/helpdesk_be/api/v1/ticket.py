from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.auth import get_current_user
from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.loggers.custom_logger import logger
from helpdesk_be.models.ticket import Ticket
from helpdesk_be.models.user import User
from helpdesk_be.repositories.ticket import get_tickets
from helpdesk_be.schemas.request.v1.ticket import CreateTicketRequest
from helpdesk_be.schemas.response.v1.ticket import (
    CreateTicketResponse,
    GetTicketsResponseItem,
)
from helpdesk_be.store.enum.ticket_status_type import TicketStatusType
from helpdesk_be.store.enum.user_role_type import UserRoleType

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreateTicketResponse)
def create_ticket(
    body: CreateTicketRequest,
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> CreateTicketResponse:
    # チケットの新規作成は社員アカウントのみ許可する
    if user.role != UserRoleType.EMPLOYEE:
        raise ForbiddenException("社員アカウントのみチケットを作成できます")

    new_ticket = Ticket(
        title=body.title,
        detail=body.detail,
        visibility=body.visibility,
        status=TicketStatusType.NEW_QUESTION,
        created_by_user_id=user.id,
    )
    session.add(new_ticket)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"failed to create ticket {e}")
        raise e

    return CreateTicketResponse(
        id=new_ticket.id,
        title=new_ticket.title,
        detail=new_ticket.detail,
        visibility=new_ticket.visibility,
        status=new_ticket.status,
        created_by_user_id=new_ticket.created_by_user_id,
        support_user_id=new_ticket.support_user_id,
    )


@router.get("", response_model=list[GetTicketsResponseItem])
def list_tickets(
    user: Annotated[User, Depends(get_current_user)],
    session: Annotated[Session, Depends(get_db)],
) -> list[GetTicketsResponseItem]:
    # SUPPORT/ADMINは全件、それ以外(将来ロールが増えた場合も含む)は「公開 または 自分が質問者」のみ閲覧可(fail-closed)
    if user.role in (UserRoleType.SUPPORT, UserRoleType.ADMIN):
        tickets = get_tickets(session)
    else:
        tickets = get_tickets(session, user_id=user.id)

    return [
        GetTicketsResponseItem(
            id=ticket.id,
            title=ticket.title,
            visibility=ticket.visibility,
            status=ticket.status,
            questioner_name=ticket.questioner.name,
            support_user_name=ticket.support_user.name if ticket.support_user else None,
            created_at=ticket.created_at,
        )
        for ticket in tickets
    ]

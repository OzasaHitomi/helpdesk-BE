from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from helpdesk_be.core.dependencies.auth import get_current_user
from helpdesk_be.core.dependencies.database import get_db
from helpdesk_be.exceptions.forbidden_exception import ForbiddenException
from helpdesk_be.loggers.custom_logger import logger
from helpdesk_be.models.ticket import Ticket
from helpdesk_be.models.user import User
from helpdesk_be.schemas.request.v1.ticket import CreateTicketRequest
from helpdesk_be.schemas.response.v1.ticket import CreateTicketResponse
from helpdesk_be.store.enum.ticket_status_type import TicketStatusType
from helpdesk_be.store.enum.user_role_type import UserRoleType

router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED)
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

    return CreateTicketResponse(id=new_ticket.id, title=new_ticket.title)

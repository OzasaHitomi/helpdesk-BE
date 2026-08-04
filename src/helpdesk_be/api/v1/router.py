from fastapi import APIRouter

from helpdesk_be.api.v1.auth import router as auth_router
from helpdesk_be.api.v1.ticket import router as ticket_router
from helpdesk_be.api.v1.ticket_comment import router as ticket_comment_router

router = APIRouter()

router.include_router(auth_router, tags=["Auth"], prefix="/auth")
router.include_router(ticket_router, tags=["Ticket"], prefix="/tickets")
# /tickets/{ticket_id}配下のネストしたリソースのため、prefixにパスパラメータを含めてincludeする
router.include_router(
    ticket_comment_router, tags=["TicketComment"], prefix="/tickets/{ticket_id}/comments"
)

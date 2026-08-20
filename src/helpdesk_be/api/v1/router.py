from fastapi import APIRouter

from helpdesk_be.api.v1.auth import router as auth_router
from helpdesk_be.api.v1.ticket import router as ticket_router
from helpdesk_be.api.v1.user import router as user_router

router = APIRouter()

router.include_router(auth_router, tags=["Auth"], prefix="/auth")
router.include_router(ticket_router, tags=["Ticket"], prefix="/tickets")
router.include_router(user_router, tags=["User"], prefix="/users")

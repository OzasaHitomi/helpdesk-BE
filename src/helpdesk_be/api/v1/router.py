from fastapi import APIRouter

from helpdesk_be.api.v1.admin.router import router as admin_router
from helpdesk_be.api.v1.auth import router as auth_router
from helpdesk_be.api.v1.ticket import router as ticket_router

router = APIRouter()

router.include_router(auth_router, tags=["Auth"], prefix="/auth")
router.include_router(ticket_router, tags=["Ticket"], prefix="/tickets")
router.include_router(admin_router, prefix="/admin")

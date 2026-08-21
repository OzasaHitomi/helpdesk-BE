from fastapi import APIRouter

from helpdesk_be.api.v1.admin.user import router as user_router

router = APIRouter()

router.include_router(user_router, tags=["User"], prefix="/users")

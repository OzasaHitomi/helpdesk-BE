from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from helpdesk_be.api.router import router as api_router
from helpdesk_be.core.config.base import core_settings
from helpdesk_be.handlers.server_exception_handler import handler as server_exception_handler
from helpdesk_be.handlers.validation_exception_handler import (
    handler as validation_exception_handler,
)

app = FastAPI()

# FEとBEはオリジンが異なる（例: :5173 と :8000）ため、
# Cookie付きのクロスオリジン通信を許可するにはCORS設定が必須
app.add_middleware(
    CORSMiddleware,
    allow_origins=[core_settings.front_end_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.add_exception_handler(RequestValidationError, validation_exception_handler)# type: ignore[arg-type]
app.add_exception_handler(Exception, server_exception_handler)

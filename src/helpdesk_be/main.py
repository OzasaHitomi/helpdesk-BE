from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from helpdesk_be.api.router import router as api_router
from helpdesk_be.core.config.base import core_settings

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

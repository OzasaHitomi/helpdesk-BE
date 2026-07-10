from fastapi import FastAPI

from helpdesk_be.api.router import router as api_router

app = FastAPI()
app.include_router(api_router, prefix="/api")

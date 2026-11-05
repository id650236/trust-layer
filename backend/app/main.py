from fastapi import FastAPI
from app.config import settings
from app.db import engine, Base
from app import models  # noqa: F401
from app.routers import principals as principals_router   
from app.routers import principals as principals_router
from app.routers import mandates as mandates_router 
from app.routers import authorize as authorize_router 

app = FastAPI(
    title="Trust Layer API",
    version="0.1.0",
    description=(
        "Trust infrastructure for autonomous AI agents. "
        "Provides identity (KYA), authorization (mandates), "
        "and tamper-evident audit receipts (SCITT)."
    ),
)

app.include_router(principals_router.router)
app.include_router(mandates_router.router)
app.include_router(authorize_router.router)
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version, "env": settings.app_env}
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from db import init_db
from services.ssh_discovery import sync_known_hosts_to_db
from routers.audit import router as audit_router
from routers.cac import router as cac_router
from routers.dashboard import router as dashboard_router
from routers.hosts import router as hosts_router
from routers.mitigate import router as mitigate_router
from routers.iso import router as iso_router
from routers.profiles import router as profiles_router
from routers.ws import router as ws_router


app = FastAPI(title="StreamGuard API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    init_db()
    sync_known_hosts_to_db()


app.include_router(cac_router, prefix="/api/cac")
app.include_router(audit_router, prefix="/api")
app.include_router(mitigate_router, prefix="/api")
app.include_router(profiles_router, prefix="/api")
app.include_router(iso_router, prefix="/api")
app.include_router(hosts_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(ws_router)

from routers.audit import router as audit_router
from routers.cac import router as cac_router
from routers.dashboard import router as dashboard_router
from routers.hosts import router as hosts_router
from routers.mitigate import router as mitigate_router
from routers.iso import router as iso_router
from routers.profiles import router as profiles_router
from routers.ws import router as ws_router

__all__ = [
    "audit_router",
    "cac_router",
    "dashboard_router",
    "hosts_router",
    "mitigate_router",
    "iso_router",
    "profiles_router",
    "ws_router",
]

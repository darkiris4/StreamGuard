from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from schemas.cac import CACCacheStatus, CACFetchResponse
from services.cac_fetch import ensure_cac_cache, get_cache_status


router = APIRouter(tags=["cac"])


class OfflineModeUpdate(BaseModel):
    offline: bool


@router.get("/fetch_stig/{distro}", response_model=CACFetchResponse)
async def fetch_stig(distro: str, offline: bool = Query(default=None)):
    try:
        repo_path, artifacts = await ensure_cac_cache(
            distro=distro, offline=settings.offline_mode if offline is None else offline
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CACFetchResponse(
        distro=distro,
        offline=settings.offline_mode if offline is None else offline,
        repo_path=str(repo_path),
        artifacts=artifacts,
    )


@router.get("/cache_status/{distro}", response_model=CACCacheStatus)
def cache_status(distro: str):
    try:
        exists, repo_path = get_cache_status(distro)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CACCacheStatus(distro=distro, cache_exists=exists, repo_path=str(repo_path))


@router.post("/offline-mode")
def set_offline_mode(payload: OfflineModeUpdate):
    settings.offline_mode = payload.offline
    return {"offline": settings.offline_mode}

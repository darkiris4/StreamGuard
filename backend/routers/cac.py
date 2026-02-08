import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from schemas.cac import (
    CACCacheStatus,
    CACFetchResponse,
    CACProfilesResponse,
    CACStatusResponse,
)
from services.cac_fetch import (
    CAC_CACHE_DIR,
    RELEASES_DIR,
    REPO_DIR,
    _products_for_distro,
    _read_metadata,
    ensure_cac_content,
    get_cache_status,
    parse_profiles_from_datastream,
)

router = APIRouter(tags=["cac"])


class OfflineModeUpdate(BaseModel):
    offline: bool


# -----------------------------------------------------------------------
# New endpoints — mounted under /api/cac via main.py prefix
# -----------------------------------------------------------------------


@router.get("/fetch/{distro}", response_model=CACFetchResponse)
async def fetch_distro(distro: str, offline: bool = Query(default=None)):
    """Trigger CAC content fetch for a specific distro.

    Online mode downloads the latest release ZIP; offline mode clones/pulls
    the full repo.  Returns the list of discovered artifacts.
    """
    use_offline = settings.offline_mode if offline is None else offline
    try:
        version, artifacts = await ensure_cac_content(
            distro=distro, offline=use_offline
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502, detail=f"Fetch failed: {exc}"
        ) from exc

    base_path = str(REPO_DIR) if use_offline else str(RELEASES_DIR / version)
    job_id = uuid.uuid4().hex[:12]

    return CACFetchResponse(
        distro=distro,
        offline=use_offline,
        repo_path=base_path,
        artifacts=artifacts,
        version=version,
        job_id=job_id,
    )


@router.get("/status", response_model=CACStatusResponse)
def cac_status():
    """Show current mode, cache version, and available distros/profiles."""
    status = get_cache_status()
    return CACStatusResponse(**status)


@router.get("/profiles/{distro}", response_model=CACProfilesResponse)
def cac_profiles(distro: str):
    """List available STIG profiles parsed from cached datastream XML."""
    try:
        profiles = parse_profiles_from_datastream(distro)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CACProfilesResponse(distro=distro, profiles=profiles)


@router.post("/offline-mode")
def set_offline_mode(payload: OfflineModeUpdate):
    """Toggle between online and offline fetch mode."""
    settings.offline_mode = payload.offline
    return {"offline": settings.offline_mode}


# -----------------------------------------------------------------------
# Legacy endpoints (backward-compatible)
# -----------------------------------------------------------------------


@router.get(
    "/fetch_stig/{distro}",
    response_model=CACFetchResponse,
    include_in_schema=False,
)
async def fetch_stig_legacy(distro: str, offline: bool = Query(default=None)):
    """Legacy wrapper — delegates to ``fetch_distro``."""
    return await fetch_distro(distro, offline)


@router.get(
    "/cache_status/{distro}",
    response_model=CACCacheStatus,
    include_in_schema=False,
)
def cache_status_legacy(distro: str):
    """Legacy single-distro cache status."""
    try:
        products = _products_for_distro(distro)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    meta = _read_metadata()
    exists = any(
        meta.get("distros", {}).get(p, {}).get("datastream")
        for p in products
    )
    return CACCacheStatus(
        distro=distro, cache_exists=exists, repo_path=str(CAC_CACHE_DIR)
    )

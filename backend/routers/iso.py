from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from services.iso_builder import build_iso


router = APIRouter(tags=["iso"])


@router.post("/build_iso")
async def build_iso_endpoint(
    distro: str = Form(...),
    base_iso: UploadFile | None = File(default=None),
    base_iso_url: str = Form(default=""),
):
    base_path: Path | None = None
    if base_iso:
        temp_path = Path("/tmp") / base_iso.filename
        temp_path.write_bytes(await base_iso.read())
        base_path = temp_path

    try:
        output_iso = build_iso(distro, base_iso_path=base_path, base_iso_url=base_iso_url)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FileResponse(path=output_iso, filename=output_iso.name)

from fastapi import APIRouter, HTTPException

from schemas.profile import ProfileCreate, ProfileResponse, ProfileUpdate
from services.profiles import (
    create_profile,
    delete_profile,
    get_profile,
    list_profiles,
    update_profile,
)


router = APIRouter(tags=["profiles"])


@router.get("/profiles", response_model=list[ProfileResponse])
def profiles_list():
    return list_profiles()


@router.post("/profiles", response_model=ProfileResponse)
def profiles_create(payload: ProfileCreate):
    return create_profile(payload)


@router.get("/profiles/{profile_id}", response_model=ProfileResponse)
def profiles_get(profile_id: int):
    profile = get_profile(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/profiles/{profile_id}", response_model=ProfileResponse)
def profiles_update(profile_id: int, payload: ProfileUpdate):
    profile = update_profile(profile_id, payload)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.delete("/profiles/{profile_id}")
def profiles_delete(profile_id: int):
    deleted = delete_profile(profile_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"status": "deleted"}

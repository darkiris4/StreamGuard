from datetime import datetime
from typing import List, Optional

from sqlmodel import Session, select

from db import get_session
from models.profile import Profile
from schemas.profile import ProfileCreate, ProfileUpdate


def create_profile(payload: ProfileCreate) -> Profile:
    session: Session = get_session()
    with session:
        profile = Profile(
            name=payload.name,
            distro=payload.distro,
            description=payload.description,
            content=payload.content,
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile


def list_profiles() -> List[Profile]:
    session: Session = get_session()
    with session:
        return list(session.exec(select(Profile)))


def get_profile(profile_id: int) -> Optional[Profile]:
    session: Session = get_session()
    with session:
        return session.get(Profile, profile_id)


def update_profile(profile_id: int, payload: ProfileUpdate) -> Optional[Profile]:
    session: Session = get_session()
    with session:
        profile = session.get(Profile, profile_id)
        if not profile:
            return None
        if payload.name is not None:
            profile.name = payload.name
        if payload.description is not None:
            profile.description = payload.description
        if payload.content is not None:
            profile.content = payload.content
        profile.updated_at = datetime.utcnow()
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return profile


def delete_profile(profile_id: int) -> bool:
    session: Session = get_session()
    with session:
        profile = session.get(Profile, profile_id)
        if not profile:
            return False
        session.delete(profile)
        session.commit()
        return True

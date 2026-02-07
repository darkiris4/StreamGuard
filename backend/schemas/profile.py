from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProfileCreate(BaseModel):
    name: str
    distro: str
    description: str = ""
    content: str


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None


class ProfileResponse(BaseModel):
    id: int
    name: str
    distro: str
    description: str
    content: str
    created_at: datetime
    updated_at: datetime

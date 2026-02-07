from datetime import datetime

from pydantic import BaseModel


class JobHistoryItem(BaseModel):
    id: int
    status: str
    host_count: int
    created_at: datetime

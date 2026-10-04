from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    title: str
    body: str
    related_id: int
    is_read: bool
    created_at: datetime


class UnreadCount(BaseModel):
    count: int

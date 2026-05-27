from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProfileInNotification(BaseModel):
    username: str | None
    full_name: str | None
    avatar_url: str | None
    is_online: bool
    last_seen: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserInNotification(BaseModel):
    id: int
    profile: ProfileInNotification

    model_config = ConfigDict(from_attributes=True)


class NotificationRead(BaseModel):
    id: int
    type: str
    entity_id: int
    entity_type: str
    is_read: bool
    created_at: datetime
    from_user: UserInNotification

    model_config = ConfigDict(from_attributes=True)


class DetailResponse(BaseModel):
    detail: str

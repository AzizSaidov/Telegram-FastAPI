from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProfileInStory(BaseModel):
    id: int
    username: str
    full_name: str | None
    avatar_url: str | None
    is_online: bool
    last_seen: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserInStory(BaseModel):
    id: int
    phone_number: str
    profile: ProfileInStory

    model_config = ConfigDict(from_attributes=True)


class StoryRead(BaseModel):
    id: int
    media_url: str
    media_type: str
    expires_at: datetime
    created_at: datetime
    user: UserInStory

    model_config = ConfigDict(from_attributes=True)


class StoryGroupRead(BaseModel):
    user: UserInStory
    stories: list[StoryRead]


class StoryViewRead(BaseModel):
    id: int
    created_at: datetime
    user: UserInStory

    model_config = ConfigDict(from_attributes=True)


class DetailResponse(BaseModel):
    detail: str

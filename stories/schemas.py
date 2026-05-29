from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProfileInStory(BaseModel):
    username: str | None
    full_name: str | None
    avatar_url: str | None
    is_online: bool
    last_seen: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserInStory(BaseModel):
    id: int
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


class StoryInGroup(BaseModel):
    id: int
    media_url: str
    media_type: str
    expires_at: datetime
    created_at: datetime
    is_viewed_by_me: bool = False
    views_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class StoryGroupRead(BaseModel):
    user: UserInStory
    stories: list[StoryInGroup]
    is_me: bool = False
    has_unviewed: bool = False
    last_story_at: datetime | None = None


class StoryViewRead(BaseModel):
    id: int
    created_at: datetime
    user: UserInStory

    model_config = ConfigDict(from_attributes=True)


class DetailResponse(BaseModel):
    detail: str

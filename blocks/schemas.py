from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class BlockUserSchema(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str):
        value = value.strip().lower()

        if not value:
            raise ValueError("Username is required")

        return value


class ProfileInBlockedUser(BaseModel):
    username: str
    full_name: str | None
    avatar_url: str | None
    is_online: bool
    last_seen: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserInBlockedUser(BaseModel):
    id: int
    profile: ProfileInBlockedUser

    model_config = ConfigDict(from_attributes=True)


class BlockedUserRead(BaseModel):
    id: int
    created_at: datetime
    blocked: UserInBlockedUser

    model_config = ConfigDict(from_attributes=True)


class DetailResponse(BaseModel):
    detail: str

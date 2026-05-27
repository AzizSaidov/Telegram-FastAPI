from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ProfileUpdateSchema(BaseModel):
    username: str | None = None
    full_name: str | None = None
    bio: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None):
        if value is None:
            return value

        value = value.strip().lower()

        if len(value) < 3 or len(value) > 30:
            raise ValueError("Username must be 3-30 characters")

        if " " in value:
            raise ValueError("Username cannot contain spaces")

        if not value.replace("_", "").isalnum():
            raise ValueError("Username can contain only letters, numbers, and underscores")

        return value

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str | None):
        if value is None:
            return value

        value = " ".join(value.strip().split())

        if not value:
            raise ValueError("Full name cannot be empty")

        if len(value) > 100:
            raise ValueError("Full name must be 100 characters or less")

        return value

    @field_validator("bio")
    @classmethod
    def validate_bio(cls, value: str | None):
        if value is None:
            return value

        value = value.strip()

        if len(value) > 255:
            raise ValueError("Bio must be 255 characters or less")

        return value


class UserInProfile(BaseModel):
    id: int
    phone_number: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileRead(BaseModel):
    id: int
    username: str
    full_name: str | None
    bio: str | None
    avatar_url: str | None
    is_online: bool
    last_seen: datetime | None
    created_at: datetime
    user: UserInProfile | None = None

    model_config = ConfigDict(from_attributes=True)

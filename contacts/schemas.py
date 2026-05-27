from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ContactCreateSchema(BaseModel):
    username: str
    name: str | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str):
        value = value.strip().lower()

        if len(value) < 3 or len(value) > 30:
            raise ValueError("Username must be 3-30 characters")

        if " " in value:
            raise ValueError("Username cannot contain spaces")

        return value

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None):
        if value is None:
            return value

        value = " ".join(value.strip().split())

        if not value:
            raise ValueError("Contact name cannot be empty")

        if len(value) > 100:
            raise ValueError("Contact name must be 100 characters or less")

        return value


class ProfileInContact(BaseModel):
    username: str
    full_name: str | None
    avatar_url: str | None
    is_online: bool
    last_seen: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserInContact(BaseModel):
    id: int
    profile: ProfileInContact

    model_config = ConfigDict(from_attributes=True)


class ContactRead(BaseModel):
    id: int
    name: str | None
    created_at: datetime
    contact: UserInContact

    model_config = ConfigDict(from_attributes=True)

class DetailResponse(BaseModel):
    detail: str

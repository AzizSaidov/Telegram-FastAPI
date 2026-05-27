from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ChannelCreateSchema(BaseModel):
    name: str
    description: str | None = None
    is_public: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        value = value.strip()

        if len(value) < 2 or len(value) > 100:
            raise ValueError("Channel name must be 2-100 characters")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None):
        if value is None:
            return value

        value = value.strip()

        if not value:
            return None

        if len(value) > 500:
            raise ValueError("Description must be at most 500 characters")

        return value


class ChannelUpdateSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None):
        if value is None:
            return value

        value = value.strip()

        if len(value) < 2 or len(value) > 100:
            raise ValueError("Channel name must be 2-100 characters")

        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str | None):
        if value is None:
            return value

        value = value.strip()

        if not value:
            return None

        if len(value) > 500:
            raise ValueError("Description must be at most 500 characters")

        return value


class ChannelMemberCreateSchema(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str):
        value = value.strip().lower()

        if not value:
            raise ValueError("Username is required")

        return value


class ChannelPostUpdateSchema(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Post text is required")

        return value


class ChannelReactionCreateSchema(BaseModel):
    emoji: str

    @field_validator("emoji")
    @classmethod
    def validate_emoji(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Emoji is required")

        if len(value) > 20:
            raise ValueError("Emoji is too long")

        return value


class ProfileInChannel(BaseModel):
    id: int
    username: str
    full_name: str | None
    avatar_url: str | None
    is_online: bool
    last_seen: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserInChannel(BaseModel):
    id: int
    phone_number: str
    profile: ProfileInChannel

    model_config = ConfigDict(from_attributes=True)


class ChannelPostPreview(BaseModel):
    id: int
    text: str | None
    media_url: str | None
    created_at: datetime
    sender: UserInChannel

    model_config = ConfigDict(from_attributes=True)


class ChannelReactionRead(BaseModel):
    id: int
    emoji: str
    created_at: datetime
    user: UserInChannel

    model_config = ConfigDict(from_attributes=True)


class ChannelPostRead(BaseModel):
    id: int
    text: str | None
    media_url: str | None
    is_edited: bool
    is_pinned: bool
    created_at: datetime
    sender: UserInChannel
    reactions: list[ChannelReactionRead] = []

    model_config = ConfigDict(from_attributes=True)


class ChannelMemberRead(BaseModel):
    id: int
    role: str
    joined_at: datetime
    user: UserInChannel

    model_config = ConfigDict(from_attributes=True)


class ChannelRead(BaseModel):
    id: int
    name: str
    avatar_url: str | None
    description: str | None
    is_public: bool
    created_at: datetime
    owner: UserInChannel
    current_user_role: str | None
    members_count: int
    last_post: ChannelPostPreview | None
    unread_count: int


class ChannelDetailRead(ChannelRead):
    members: list[ChannelMemberRead]


class MembersCountRead(BaseModel):
    count: int


class DetailResponse(BaseModel):
    detail: str

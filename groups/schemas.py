from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class GroupCreateSchema(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str):
        value = value.strip()

        if len(value) < 2 or len(value) > 100:
            raise ValueError("Group name must be 2-100 characters")

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


class GroupUpdateSchema(BaseModel):
    name: str | None = None
    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None):
        if value is None:
            return value

        value = value.strip()

        if len(value) < 2 or len(value) > 100:
            raise ValueError("Group name must be 2-100 characters")

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


class GroupMemberCreateSchema(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str):
        value = value.strip().lower()

        if not value:
            raise ValueError("Username is required")

        return value


class GroupMessageUpdateSchema(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Message text is required")

        return value


class GroupReactionCreateSchema(BaseModel):
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


class ProfileInGroup(BaseModel):
    username: str | None
    full_name: str | None
    avatar_url: str | None
    is_online: bool
    last_seen: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserInGroup(BaseModel):
    id: int
    profile: ProfileInGroup

    model_config = ConfigDict(from_attributes=True)


class GroupMessagePreview(BaseModel):
    id: int
    text: str | None
    media_url: str | None
    created_at: datetime
    sender: UserInGroup

    model_config = ConfigDict(from_attributes=True)


class GroupReactionRead(BaseModel):
    id: int
    emoji: str
    created_at: datetime
    user: UserInGroup

    model_config = ConfigDict(from_attributes=True)


class GroupMessageRead(BaseModel):
    id: int
    text: str | None
    media_url: str | None
    reply_to: GroupMessagePreview | None
    forwarded_from: GroupMessagePreview | None
    is_edited: bool
    is_pinned: bool
    created_at: datetime
    sender: UserInGroup
    reactions: list[GroupReactionRead] = []

    model_config = ConfigDict(from_attributes=True)


class GroupMemberRead(BaseModel):
    id: int
    role: str
    joined_at: datetime
    user: UserInGroup

    model_config = ConfigDict(from_attributes=True)


class GroupRead(BaseModel):
    id: int
    name: str
    avatar_url: str | None
    description: str | None
    created_at: datetime
    owner: UserInGroup
    current_user_role: str
    members_count: int
    last_message: GroupMessagePreview | None
    unread_count: int


class GroupDetailRead(GroupRead):
    members: list[GroupMemberRead]


class MembersCountRead(BaseModel):
    count: int


class DetailResponse(BaseModel):
    detail: str

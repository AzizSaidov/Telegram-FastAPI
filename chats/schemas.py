from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class ChatCreateSchema(BaseModel):
    username: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str):
        value = value.strip().lower()

        if not value:
            raise ValueError("Username is required")

        return value


class MessageUpdateSchema(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Message text is required")

        return value


class ReactionCreateSchema(BaseModel):
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


class ProfileInChat(BaseModel):
    username: str | None
    full_name: str | None
    avatar_url: str | None
    is_online: bool
    last_seen: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserInChat(BaseModel):
    id: int
    profile: ProfileInChat

    model_config = ConfigDict(from_attributes=True)


class MessagePreview(BaseModel):
    id: int
    text: str | None
    media_url: str | None
    created_at: datetime
    sender: UserInChat

    model_config = ConfigDict(from_attributes=True)


class MessageReactionRead(BaseModel):
    id: int
    emoji: str
    created_at: datetime
    user: UserInChat

    model_config = ConfigDict(from_attributes=True)


class MessageRead(BaseModel):
    id: int
    text: str | None
    media_url: str | None
    reply_to: MessagePreview | None
    forwarded_from: MessagePreview | None
    is_edited: bool
    is_read: bool
    is_pinned: bool
    created_at: datetime
    sender: UserInChat
    reactions: list[MessageReactionRead] = []

    model_config = ConfigDict(from_attributes=True)


class ChatRead(BaseModel):
    id: int
    created_at: datetime
    other_user: UserInChat
    last_message: MessagePreview | None
    unread_count: int


class UnifiedLastMessageRead(BaseModel):
    id: int
    text: str | None
    media_url: str | None
    created_at: datetime
    sender: UserInChat

    model_config = ConfigDict(from_attributes=True)


class UnifiedChatRead(BaseModel):
    id: int
    type: str
    title: str
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime
    unread_count: int
    last_message: UnifiedLastMessageRead | None
    user: UserInChat | None = None
    members_count: int | None = None
    current_user_role: str | None = None
    is_online: bool | None = None
    last_seen: datetime | None = None
    is_public: bool | None = None


class DetailResponse(BaseModel):
    detail: str

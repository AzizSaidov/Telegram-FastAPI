from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class UserRegisterSchema(BaseModel):
    phone_number: str
    username: str
    full_name: str
    password: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str):
        value = value.strip()

        if not value.startswith("+"):
            raise ValueError("Phone number must start with +")

        phone_digits = value[1:]

        if not phone_digits.isdigit() or len(phone_digits) < 9 or len(phone_digits) > 20:
            raise ValueError("Phone number must contain 9-20 digits after +")

        return value

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str):
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
    def validate_full_name(cls, value: str):
        value = " ".join(value.strip().split())

        if not value:
            raise ValueError("Full name is required")

        if len(value) > 100:
            raise ValueError("Full name must be 100 characters or less")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters")

        return value


class UserLoginSchema(BaseModel):
    phone_number: str
    password: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Phone number is required")

        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str):
        if not value:
            raise ValueError("Password is required")

        return value


class ProfileInUser(BaseModel):
    username: str
    full_name: str | None
    bio: str | None
    avatar_url: str | None
    is_online: bool
    last_seen: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UserRead(BaseModel):
    id: int
    phone_number: str
    created_at: datetime
    profile: ProfileInUser

    model_config = ConfigDict(from_attributes=True)


class UserSearchRead(BaseModel):
    id: int
    created_at: datetime
    profile: ProfileInUser

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: UserRead


class LogoutResponse(BaseModel):
    detail: str

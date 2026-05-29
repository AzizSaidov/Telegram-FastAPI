from datetime import datetime
import re

from pydantic import BaseModel, ConfigDict, field_validator


class PhoneNumberSchema(BaseModel):
    phone_number: str

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


class VerifyOTPSchema(PhoneNumberSchema):
    otp_code: str

    @field_validator("otp_code")
    @classmethod
    def validate_otp_code(cls, value: str):
        value = value.strip()

        if not value.isdigit() or len(value) != 6:
            raise ValueError("OTP code must contain 6 digits")

        return value


class RegisterRequestSchema(PhoneNumberSchema):
    full_name: str
    username: str | None = None

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, value: str):
        value = value.strip()

        if len(value) < 2:
            raise ValueError("Full name must contain at least 2 characters")

        if len(value) > 100:
            raise ValueError("Full name is too long")

        return value

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str | None):
        if value is None:
            return value

        value = value.strip().lower().lstrip("@")

        if not value:
            return None

        if len(value) < 5 or len(value) > 30:
            raise ValueError("Username must contain 5-30 characters")

        if not re.fullmatch(r"[a-z0-9_]+", value):
            raise ValueError("Username can contain only letters, numbers and underscores")

        return value


class RegisterVerifyOTPSchema(VerifyOTPSchema, RegisterRequestSchema):
    pass


class OTPResponse(BaseModel):
    detail: str
    phone_number: str
    otp_code: str
    expires_at: datetime


class ProfileInUser(BaseModel):
    username: str | None
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
    phone_number: str
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

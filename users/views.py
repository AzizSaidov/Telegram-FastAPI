from datetime import timedelta
from secrets import randbelow

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from profiles.models import Profile
from users.auth import create_access_token, create_refresh_token
from users.models import OTPCode, User
from users.schemas import PhoneNumberSchema, RegisterRequestSchema, RegisterVerifyOTPSchema, VerifyOTPSchema
from utils import get_dushanbe_time


OTP_EXPIRE_MINUTES = 5


def generate_otp_code():
    return str(randbelow(900000) + 100000)


def create_otp_for_phone(phone_number: str, db: Session, detail: str):
    db.query(OTPCode).filter(
        OTPCode.phone_number == phone_number,
        OTPCode.is_used == False,
    ).update({"is_used": True})

    expires_at = get_dushanbe_time() + timedelta(minutes=OTP_EXPIRE_MINUTES)
    otp = OTPCode(
        phone_number=phone_number,
        code=generate_otp_code(),
        expires_at=expires_at,
    )

    db.add(otp)
    db.commit()
    db.refresh(otp)

    return {
        "detail": detail,
        "phone_number": otp.phone_number,
        "otp_code": otp.code,
        "expires_at": otp.expires_at,
    }


def get_valid_otp(data: VerifyOTPSchema, db: Session):
    now = get_dushanbe_time()
    otp = db.query(OTPCode).filter(
        OTPCode.phone_number == data.phone_number,
        OTPCode.code == data.otp_code,
        OTPCode.is_used == False,
        OTPCode.expires_at > now,
    ).order_by(OTPCode.created_at.desc()).first()

    if otp is None:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP code")

    return otp


def get_user_by_phone_or_404(phone_number: str, db: Session):
    user = db.query(User).filter(User.phone_number == phone_number).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found. Please register first")

    return user


def ensure_phone_is_available(phone_number: str, db: Session):
    user = db.query(User).filter(User.phone_number == phone_number).first()

    if user is not None:
        raise HTTPException(status_code=409, detail="Phone number is already registered")


def ensure_username_is_available(username: str | None, db: Session):
    if not username:
        return

    profile = db.query(Profile).filter(Profile.username == username).first()

    if profile is not None:
        raise HTTPException(status_code=409, detail="Username is already taken")


def build_auth_response(user: User, profile: Profile):
    user.profile = profile

    access_token = create_access_token(data={"user_id": user.id})
    refresh_token = create_refresh_token(data={"user_id": user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }


def request_login_otp(data: PhoneNumberSchema, db: Session):
    get_user_by_phone_or_404(data.phone_number, db)
    return create_otp_for_phone(data.phone_number, db, "Login OTP code created")


def verify_login_otp(data: VerifyOTPSchema, db: Session):
    user = get_user_by_phone_or_404(data.phone_number, db)
    otp = get_valid_otp(data, db)

    profile = db.query(Profile).filter(Profile.user_id == user.id).first()

    if profile is None:
        profile = Profile(
            user_id=user.id,
            is_online=True,
        )
        db.add(profile)
    else:
        profile.is_online = True

    otp.is_used = True

    db.commit()
    db.refresh(user)
    db.refresh(profile)

    return build_auth_response(user, profile)


def request_register_otp(data: RegisterRequestSchema, db: Session):
    ensure_phone_is_available(data.phone_number, db)
    ensure_username_is_available(data.username, db)

    return create_otp_for_phone(data.phone_number, db, "Registration OTP code created")


def verify_register_otp(data: RegisterVerifyOTPSchema, db: Session):
    ensure_phone_is_available(data.phone_number, db)
    ensure_username_is_available(data.username, db)
    otp = get_valid_otp(data, db)

    user = User(phone_number=data.phone_number)
    db.add(user)
    db.flush()

    profile = Profile(
        user_id=user.id,
        username=data.username,
        full_name=data.full_name,
        is_online=True,
    )
    db.add(profile)

    otp.is_used = True

    db.commit()
    db.refresh(user)
    db.refresh(profile)

    return build_auth_response(user, profile)


def logout_user(db: Session, user_id: int):
    from profiles.models import Profile

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile.is_online = False
    profile.last_seen = get_dushanbe_time()

    db.commit()

    return {"detail": "Logout successful"}


def clean_phone_number(phone_number: str):
    phone_number = phone_number.strip()

    if not phone_number.startswith("+"):
        raise HTTPException(status_code=400, detail="Phone number must start with +")

    phone_digits = phone_number[1:]

    if not phone_digits.isdigit() or len(phone_digits) < 9 or len(phone_digits) > 20:
        raise HTTPException(status_code=400, detail="Phone number must contain 9-20 digits after +")

    return phone_number


def search_user_by_phone(phone_number: str, db: Session, current_user: User):
    phone_number = clean_phone_number(phone_number)

    user = db.query(User).filter(
        User.phone_number == phone_number,
        User.id != current_user.id,
    ).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def search_users(q: str, db: Session, current_user: User):
    query = q.strip().lower()

    if not query:
        raise HTTPException(status_code=400, detail="Search query is required")

    filters = [
        Profile.username.ilike(f"%{query}%"),
        Profile.full_name.ilike(f"%{query}%"),
    ]

    if query.startswith("+"):
        filters.append(User.phone_number == query)

    return db.query(User).join(Profile).filter(
        User.id != current_user.id,
        or_(*filters),
    ).limit(20).all()

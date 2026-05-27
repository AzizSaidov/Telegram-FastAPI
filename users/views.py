from datetime import timedelta
from secrets import randbelow

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from profiles.models import Profile
from users.auth import create_access_token, create_refresh_token
from users.models import OTPCode, User
from users.schemas import PhoneNumberSchema, VerifyOTPSchema
from utils import get_dushanbe_time


OTP_EXPIRE_MINUTES = 5


def generate_otp_code():
    return str(randbelow(900000) + 100000)


def request_otp(data: PhoneNumberSchema, db: Session):
    db.query(OTPCode).filter(
        OTPCode.phone_number == data.phone_number,
        OTPCode.is_used == False,
    ).update({"is_used": True})

    expires_at = get_dushanbe_time() + timedelta(minutes=OTP_EXPIRE_MINUTES)
    otp = OTPCode(
        phone_number=data.phone_number,
        code=generate_otp_code(),
        expires_at=expires_at,
    )

    db.add(otp)
    db.commit()
    db.refresh(otp)

    return {
        "detail": "OTP code created",
        "phone_number": otp.phone_number,
        "otp_code": otp.code,
        "expires_at": otp.expires_at,
    }


def verify_otp(data: VerifyOTPSchema, db: Session):
    now = get_dushanbe_time()
    otp = db.query(OTPCode).filter(
        OTPCode.phone_number == data.phone_number,
        OTPCode.code == data.otp_code,
        OTPCode.is_used == False,
        OTPCode.expires_at > now,
    ).order_by(OTPCode.created_at.desc()).first()

    if otp is None:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP code")

    user = db.query(User).filter(User.phone_number == data.phone_number).first()

    if user is None:
        user = User(
            phone_number=data.phone_number,
        )
        db.add(user)
        db.flush()

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

    user.profile = profile

    access_token = create_access_token(data={"user_id": user.id})
    refresh_token = create_refresh_token(data={"user_id": user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user,
    }


def logout_user(db: Session, user_id: int):
    from profiles.models import Profile

    profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile.is_online = False
    profile.last_seen = get_dushanbe_time()

    db.commit()

    return {"detail": "Logout successful"}


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

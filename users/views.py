from fastapi import HTTPException
from sqlalchemy.orm import Session

from users.auth import create_access_token, create_refresh_token, hash_password, verify_password
from users.models import User
from users.schemas import UserLoginSchema, UserRegisterSchema
from utils import get_dushanbe_time


def register_user(data: UserRegisterSchema, db: Session):
    from profiles.models import Profile

    existing_user = db.query(User).filter(User.phone_number == data.phone_number).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Phone number already exists")

    existing_profile = db.query(Profile).filter(Profile.username == data.username).first()

    if existing_profile:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        phone_number=data.phone_number,
        hashed_password=hash_password(data.password),
    )

    db.add(new_user)
    db.flush()

    new_profile = Profile(
        user_id=new_user.id,
        username=data.username,
        full_name=data.full_name,
        is_online=True,
    )

    db.add(new_profile)
    db.commit()
    db.refresh(new_user)
    db.refresh(new_profile)

    new_user.profile = new_profile

    access_token = create_access_token(data={"user_id": new_user.id})
    refresh_token = create_refresh_token(data={"user_id": new_user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": new_user,
    }


def login_user(data: UserLoginSchema, db: Session):
    from profiles.models import Profile

    user = db.query(User).filter(User.phone_number == data.phone_number).first()

    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid phone number or password")

    profile = db.query(Profile).filter(Profile.user_id == user.id).first()

    if profile:
        profile.is_online = True
        db.commit()
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

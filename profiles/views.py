import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from profiles.models import Profile
from profiles.schemas import ProfileUpdateSchema


AVATARS_DIR = Path("media") / "avatars"


def save_avatar(avatar: UploadFile):
    if avatar.content_type is None or not avatar.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Avatar must be an image")

    AVATARS_DIR.mkdir(parents=True, exist_ok=True)

    file_suffix = Path(avatar.filename or "").suffix.lower()

    if file_suffix not in [".jpg", ".jpeg", ".png", ".webp"]:
        file_suffix = ".jpg"

    file_name = f"{uuid4().hex}{file_suffix}"
    file_path = AVATARS_DIR / file_name

    with file_path.open("wb") as file:
        shutil.copyfileobj(avatar.file, file)

    return f"/media/avatars/{file_name}"


def get_my_profile(db: Session, user_id: int):
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


def get_profile_by_username(username: str, db: Session):
    profile = db.query(Profile).filter(Profile.username == username.lower()).first()

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


def update_my_profile(data: ProfileUpdateSchema, db: Session, user_id: int, avatar: UploadFile | None = None):
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    if data.username is not None and data.username != profile.username:
        existing_profile = db.query(Profile).filter(Profile.username == data.username).first()

        if existing_profile:
            raise HTTPException(status_code=400, detail="Username already exists")

        profile.username = data.username

    if data.full_name is not None:
        profile.full_name = data.full_name

    if data.bio is not None:
        profile.bio = data.bio

    if avatar is not None:
        profile.avatar_url = save_avatar(avatar)

    db.commit()
    db.refresh(profile)

    return profile

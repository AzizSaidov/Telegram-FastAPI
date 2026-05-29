from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import get_db
from profiles.schemas import MyProfileRead, ProfileRead, ProfileUpdateSchema
from profiles.views import get_my_profile, get_profile_by_username, update_my_profile
from users.auth import get_current_user
from users.models import User


profiles_router = APIRouter(prefix="/profiles", tags=["Profiles"])


@profiles_router.get("/me", response_model=MyProfileRead)
def my_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_my_profile(db, current_user.id)


@profiles_router.put("/me", response_model=MyProfileRead)
def update_profile(
    username: str | None = Form(None),
    full_name: str | None = Form(None),
    bio: str | None = Form(None),
    avatar: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        data = ProfileUpdateSchema(
            username=username,
            full_name=full_name,
            bio=bio,
        )
    except ValidationError as e:
        errors = e.errors()
        msg = errors[0]["msg"].replace("Value error, ", "") if errors else "Validation error"
        raise HTTPException(status_code=422, detail=msg)

    return update_my_profile(data, db, current_user.id, avatar)


@profiles_router.get("/{username}", response_model=ProfileRead)
def profile_detail(username: str, db: Session = Depends(get_db)):
    return get_profile_by_username(username, db)

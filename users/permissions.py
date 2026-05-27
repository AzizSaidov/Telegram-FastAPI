from fastapi import HTTPException
from sqlalchemy.orm import Session

from profiles.models import Profile
from users.models import User


def get_current_profile(db: Session, current_user: User):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


def is_current_user(profile: Profile, current_user: User):
    return profile.user_id == current_user.id


def check_current_user(profile: Profile, current_user: User):
    if not is_current_user(profile, current_user):
        raise HTTPException(status_code=403, detail="Permission denied")

    return True


def is_blocked(db: Session, blocker_id: int, blocked_id: int):
    from blocks.models import BlockedUser

    blocked_user = db.query(BlockedUser).filter(
        BlockedUser.blocker_id == blocker_id,
        BlockedUser.blocked_id == blocked_id,
    ).first()

    return blocked_user is not None

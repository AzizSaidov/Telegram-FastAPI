from fastapi import HTTPException
from sqlalchemy.orm import Session

from blocks.models import BlockedUser
from blocks.schemas import BlockUserSchema
from profiles.models import Profile
from users.models import User


def get_blocked_users(db: Session, current_user: User):
    return db.query(BlockedUser).filter(BlockedUser.blocker_id == current_user.id).all()


def block_user(data: BlockUserSchema, db: Session, current_user: User):
    blocked_profile = db.query(Profile).filter(Profile.username == data.username).first()

    if blocked_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    blocked_user = db.query(User).filter(User.id == blocked_profile.user_id).first()

    if blocked_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if blocked_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot block yourself")

    existing_block = db.query(BlockedUser).filter(
        BlockedUser.blocker_id == current_user.id,
        BlockedUser.blocked_id == blocked_user.id,
    ).first()

    if existing_block:
        raise HTTPException(status_code=400, detail="User already blocked")

    new_block = BlockedUser(
        blocker_id=current_user.id,
        blocked_id=blocked_user.id,
    )

    db.add(new_block)
    db.commit()
    db.refresh(new_block)

    return new_block


def unblock_user(username: str, db: Session, current_user: User):
    blocked_profile = db.query(Profile).filter(Profile.username == username.lower()).first()

    if blocked_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    blocked_user = db.query(BlockedUser).filter(
        BlockedUser.blocker_id == current_user.id,
        BlockedUser.blocked_id == blocked_profile.user_id,
    ).first()

    if blocked_user is None:
        raise HTTPException(status_code=404, detail="Blocked user not found")

    db.delete(blocked_user)
    db.commit()

    return {"detail": "User unblocked successfully"}

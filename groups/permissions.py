from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from blocks.models import BlockedUser
from groups.models import Group, GroupMember
from users.models import User


GROUP_ADMIN = "admin"
GROUP_MEMBER = "member"


def get_group_member(group_id: int, user_id: int, db: Session):
    return db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.user_id == user_id,
    ).first()


def check_group_member(group: Group, current_user: User, db: Session):
    member = get_group_member(group.id, current_user.id, db)

    if member is None:
        raise HTTPException(status_code=403, detail="You are not a group member")

    return member


def check_group_admin(group: Group, current_user: User, db: Session):
    member = check_group_member(group, current_user, db)

    if member.role != GROUP_ADMIN:
        raise HTTPException(status_code=403, detail="Only group admin can do this")

    return member


def check_group_block(db: Session, current_user_id: int, target_user_id: int):
    blocked = db.query(BlockedUser).filter(
        or_(
            (BlockedUser.blocker_id == current_user_id) & (BlockedUser.blocked_id == target_user_id),
            (BlockedUser.blocker_id == target_user_id) & (BlockedUser.blocked_id == current_user_id),
        )
    ).first()

    if blocked:
        raise HTTPException(status_code=403, detail="You cannot add this user")

    return True

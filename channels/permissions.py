from fastapi import HTTPException
from sqlalchemy.orm import Session

from channels.models import Channel, ChannelMember
from users.models import User


CHANNEL_ADMIN = "admin"
CHANNEL_SUBSCRIBER = "subscriber"


def get_channel_member(channel_id: int, user_id: int, db: Session):
    return db.query(ChannelMember).filter(
        ChannelMember.channel_id == channel_id,
        ChannelMember.user_id == user_id,
    ).first()


def check_channel_member(channel: Channel, current_user: User, db: Session):
    member = get_channel_member(channel.id, current_user.id, db)

    if member is None:
        raise HTTPException(status_code=403, detail="You are not a channel member")

    return member


def check_channel_admin(channel: Channel, current_user: User, db: Session):
    member = check_channel_member(channel, current_user, db)

    if member.role != CHANNEL_ADMIN:
        raise HTTPException(status_code=403, detail="Only channel admin can do this")

    return member


def check_channel_visible(channel: Channel, current_user: User, db: Session):
    member = get_channel_member(channel.id, current_user.id, db)

    if channel.is_public or member is not None:
        return member

    raise HTTPException(status_code=403, detail="You cannot view this channel")

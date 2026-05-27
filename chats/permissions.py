from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from blocks.models import BlockedUser
from chats.models import Chat
from users.models import User


def get_other_user(chat: Chat, current_user: User):
    if chat.user_id_1 == current_user.id:
        return chat.user_2

    return chat.user_1


def check_chat_member(chat: Chat, current_user: User):
    if current_user.id not in [chat.user_id_1, chat.user_id_2]:
        raise HTTPException(status_code=403, detail="You are not a chat member")

    return True


def check_private_chat_block(db: Session, sender_id: int, receiver_id: int):
    blocked = db.query(BlockedUser).filter(
        or_(
            (BlockedUser.blocker_id == sender_id) & (BlockedUser.blocked_id == receiver_id),
            (BlockedUser.blocker_id == receiver_id) & (BlockedUser.blocked_id == sender_id),
        )
    ).first()

    if blocked:
        raise HTTPException(status_code=403, detail="You cannot use this chat")

    return True

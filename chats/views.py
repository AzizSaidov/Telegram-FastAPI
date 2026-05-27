import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import or_
from sqlalchemy.orm import Session

from channels.models import ChannelMember, ChannelPost
from channels.views import get_channel_unread_count
from chats.models import Chat, Message, MessageReaction
from chats.permissions import check_chat_member, check_private_chat_block, get_other_user
from chats.schemas import ChatCreateSchema, MessageUpdateSchema, ReactionCreateSchema
from groups.models import GroupMember, GroupMessage
from groups.views import get_group_unread_count
from notifications.views import create_notification
from profiles.models import Profile
from sockets.schemas import EVENT_MESSAGE_CREATED, EVENT_MESSAGE_DELETED, EVENT_MESSAGE_UPDATED, EVENT_REACTION_CREATED, socket_event
from sockets.utils import broadcast_socket_event_to_users
from users.models import User


CHAT_PHOTOS_DIR = Path("media") / "chats" / "photos"
CHAT_VIDEOS_DIR = Path("media") / "chats" / "videos"


def build_message_event_data(message: Message):
    return {
        "id": message.id,
        "chat_id": message.chat_id,
        "sender_id": message.sender_id,
        "text": message.text,
        "media_url": message.media_url,
        "reply_to_id": message.reply_to_id,
        "forwarded_from_id": message.forwarded_from_id,
        "is_edited": message.is_edited,
        "is_read": message.is_read,
        "is_pinned": message.is_pinned,
        "created_at": message.created_at.isoformat(),
    }


def get_chat_or_404(chat_id: int, db: Session):
    chat = db.query(Chat).filter(Chat.id == chat_id).first()

    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    return chat


def get_message_or_404(message_id: int, db: Session):
    message = db.query(Message).filter(Message.id == message_id).first()

    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    return message


def save_chat_media(media: UploadFile):
    if media.content_type is None:
        raise HTTPException(status_code=400, detail="Media file is required")

    if media.content_type.startswith("image/"):
        media_type = "photos"
        media_dir = CHAT_PHOTOS_DIR
        allowed_suffixes = [".jpg", ".jpeg", ".png", ".webp"]
        default_suffix = ".jpg"
    elif media.content_type.startswith("video/"):
        media_type = "videos"
        media_dir = CHAT_VIDEOS_DIR
        allowed_suffixes = [".mp4", ".mov", ".webm"]
        default_suffix = ".mp4"
    else:
        raise HTTPException(status_code=400, detail="Message media must be photo or video")

    media_dir.mkdir(parents=True, exist_ok=True)

    file_suffix = Path(media.filename or "").suffix.lower()

    if file_suffix not in allowed_suffixes:
        file_suffix = default_suffix

    file_name = f"{uuid4().hex}{file_suffix}"
    file_path = media_dir / file_name

    with file_path.open("wb") as file:
        shutil.copyfileobj(media.file, file)

    return f"/media/chats/{media_type}/{file_name}"


def build_chat_response(chat: Chat, current_user: User, db: Session):
    last_message = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at.desc()).first()
    unread_count = db.query(Message).filter(
        Message.chat_id == chat.id,
        Message.sender_id != current_user.id,
        Message.is_read == False,
    ).count()

    return {
        "id": chat.id,
        "created_at": chat.created_at,
        "other_user": get_other_user(chat, current_user),
        "last_message": last_message,
        "unread_count": unread_count,
    }


def get_chats(db: Session, current_user: User):
    chats = db.query(Chat).filter(
        or_(
            Chat.user_id_1 == current_user.id,
            Chat.user_id_2 == current_user.id,
        )
    ).all()

    return sorted(
        [build_chat_response(chat, current_user, db) for chat in chats],
        key=lambda chat: chat["last_message"].created_at if chat["last_message"] else chat["created_at"],
        reverse=True,
    )


def build_unified_last_message(message):
    if message is None:
        return None

    return {
        "id": message.id,
        "text": message.text,
        "media_url": message.media_url,
        "created_at": message.created_at,
        "sender": message.sender,
    }


def get_unified_chats(db: Session, current_user: User):
    items = []
    private_chats = db.query(Chat).filter(
        or_(
            Chat.user_id_1 == current_user.id,
            Chat.user_id_2 == current_user.id,
        )
    ).all()

    for chat in private_chats:
        other_user = get_other_user(chat, current_user)
        other_profile = other_user.profile
        last_message = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at.desc()).first()
        unread_count = db.query(Message).filter(
            Message.chat_id == chat.id,
            Message.sender_id != current_user.id,
            Message.is_read == False,
        ).count()

        items.append({
            "id": chat.id,
            "type": "private",
        "title": other_profile.full_name or other_profile.username or f"User {other_user.id}",
            "avatar_url": other_profile.avatar_url,
            "created_at": chat.created_at,
            "updated_at": last_message.created_at if last_message else chat.created_at,
            "unread_count": unread_count,
            "last_message": build_unified_last_message(last_message),
            "user": other_user,
            "members_count": None,
            "current_user_role": None,
            "is_online": other_profile.is_online,
            "last_seen": other_profile.last_seen,
            "is_public": None,
        })

    group_memberships = db.query(GroupMember).filter(GroupMember.user_id == current_user.id).all()

    for membership in group_memberships:
        group = membership.group
        last_message = db.query(GroupMessage).filter(GroupMessage.group_id == group.id).order_by(GroupMessage.created_at.desc()).first()
        members_count = db.query(GroupMember).filter(GroupMember.group_id == group.id).count()

        items.append({
            "id": group.id,
            "type": "group",
            "title": group.name,
            "avatar_url": group.avatar_url,
            "created_at": group.created_at,
            "updated_at": last_message.created_at if last_message else group.created_at,
            "unread_count": get_group_unread_count(group.id, current_user, db),
            "last_message": build_unified_last_message(last_message),
            "user": None,
            "members_count": members_count,
            "current_user_role": membership.role,
            "is_online": None,
            "last_seen": None,
            "is_public": None,
        })

    channel_memberships = db.query(ChannelMember).filter(ChannelMember.user_id == current_user.id).all()

    for membership in channel_memberships:
        channel = membership.channel
        last_post = db.query(ChannelPost).filter(ChannelPost.channel_id == channel.id).order_by(ChannelPost.created_at.desc()).first()
        members_count = db.query(ChannelMember).filter(ChannelMember.channel_id == channel.id).count()

        items.append({
            "id": channel.id,
            "type": "channel",
            "title": channel.name,
            "avatar_url": channel.avatar_url,
            "created_at": channel.created_at,
            "updated_at": last_post.created_at if last_post else channel.created_at,
            "unread_count": get_channel_unread_count(channel.id, current_user, db),
            "last_message": build_unified_last_message(last_post),
            "user": None,
            "members_count": members_count,
            "current_user_role": membership.role,
            "is_online": None,
            "last_seen": None,
            "is_public": channel.is_public,
        })

    return sorted(items, key=lambda item: item["updated_at"], reverse=True)


def search_unified_chats(q: str, db: Session, current_user: User):
    query = q.strip().lower()

    if not query:
        raise HTTPException(status_code=400, detail="Search query is required")

    items = get_unified_chats(db, current_user)
    result = []

    for item in items:
        title = item["title"].lower()
        username = ""

        if item["user"] and item["user"].profile:
            username = item["user"].profile.username.lower()

        if query in title or query in username:
            result.append(item)

    return result


def create_or_get_chat(data: ChatCreateSchema, db: Session, current_user: User):
    profile = db.query(Profile).filter(Profile.username == data.username).first()

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    other_user = db.query(User).filter(User.id == profile.user_id).first()

    if other_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if other_user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot create chat with yourself")

    check_private_chat_block(db, current_user.id, other_user.id)

    user_id_1 = min(current_user.id, other_user.id)
    user_id_2 = max(current_user.id, other_user.id)

    chat = db.query(Chat).filter(
        Chat.user_id_1 == user_id_1,
        Chat.user_id_2 == user_id_2,
    ).first()

    if chat is None:
        chat = Chat(
            user_id_1=user_id_1,
            user_id_2=user_id_2,
        )
        db.add(chat)
        db.commit()
        db.refresh(chat)

    return build_chat_response(chat, current_user, db)


def get_chat_messages(chat_id: int, db: Session, current_user: User, limit: int, offset: int):
    chat = get_chat_or_404(chat_id, db)
    check_chat_member(chat, current_user)

    db.query(Message).filter(
        Message.chat_id == chat.id,
        Message.sender_id != current_user.id,
        Message.is_read == False,
    ).update({"is_read": True})
    db.commit()

    return db.query(Message).filter(
        Message.chat_id == chat.id,
    ).order_by(Message.created_at.desc()).offset(offset).limit(limit).all()


def send_message(
    chat_id: int,
    text: str | None,
    reply_to_id: int | None,
    forwarded_from_id: int | None,
    media: UploadFile | None,
    db: Session,
    current_user: User,
):
    chat = get_chat_or_404(chat_id, db)
    check_chat_member(chat, current_user)
    other_user = get_other_user(chat, current_user)
    check_private_chat_block(db, current_user.id, other_user.id)

    message_text = text.strip() if text is not None else None
    media_url = save_chat_media(media) if media is not None else None
    forwarded_from = None

    if reply_to_id is not None:
        reply_to = get_message_or_404(reply_to_id, db)

        if reply_to.chat_id != chat.id:
            raise HTTPException(status_code=400, detail="Reply message is not from this chat")

    if forwarded_from_id is not None:
        forwarded_from = get_message_or_404(forwarded_from_id, db)

        if message_text is None and media_url is None:
            message_text = forwarded_from.text
            media_url = forwarded_from.media_url

    if not message_text and media_url is None:
        raise HTTPException(status_code=400, detail="Message text or media is required")

    new_message = Message(
        chat_id=chat.id,
        sender_id=current_user.id,
        text=message_text,
        media_url=media_url,
        reply_to_id=reply_to_id,
        forwarded_from_id=forwarded_from.id if forwarded_from else None,
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    create_notification(db, other_user.id, current_user.id, "message", new_message.id, "message")
    broadcast_socket_event_to_users(
        [current_user.id, other_user.id],
        socket_event(EVENT_MESSAGE_CREATED, build_message_event_data(new_message)),
    )

    return new_message


def edit_message(chat_id: int, message_id: int, data: MessageUpdateSchema, db: Session, current_user: User):
    chat = get_chat_or_404(chat_id, db)
    check_chat_member(chat, current_user)
    message = get_message_or_404(message_id, db)

    if message.chat_id != chat.id:
        raise HTTPException(status_code=404, detail="Message not found in this chat")

    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can edit only your own message")

    message.text = data.text
    message.is_edited = True

    db.commit()
    db.refresh(message)

    other_user = get_other_user(chat, current_user)
    broadcast_socket_event_to_users(
        [current_user.id, other_user.id],
        socket_event(EVENT_MESSAGE_UPDATED, build_message_event_data(message)),
    )

    return message


def delete_message(chat_id: int, message_id: int, db: Session, current_user: User):
    chat = get_chat_or_404(chat_id, db)
    check_chat_member(chat, current_user)
    message = get_message_or_404(message_id, db)

    if message.chat_id != chat.id:
        raise HTTPException(status_code=404, detail="Message not found in this chat")

    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can delete only your own message")

    other_user = get_other_user(chat, current_user)
    event_data = {
        "id": message.id,
        "chat_id": chat.id,
    }

    db.query(Message).filter(Message.reply_to_id == message.id).update({"reply_to_id": None})
    db.query(Message).filter(Message.forwarded_from_id == message.id).update({"forwarded_from_id": None})
    db.query(MessageReaction).filter(MessageReaction.message_id == message.id).delete()
    db.delete(message)
    db.commit()

    broadcast_socket_event_to_users(
        [current_user.id, other_user.id],
        socket_event(EVENT_MESSAGE_DELETED, event_data),
    )

    return {"detail": "Message deleted successfully"}


def pin_message(chat_id: int, message_id: int, db: Session, current_user: User):
    chat = get_chat_or_404(chat_id, db)
    check_chat_member(chat, current_user)
    message = get_message_or_404(message_id, db)

    if message.chat_id != chat.id:
        raise HTTPException(status_code=404, detail="Message not found in this chat")

    db.query(Message).filter(
        Message.chat_id == chat.id,
        Message.is_pinned == True,
    ).update({"is_pinned": False})

    message.is_pinned = True

    db.commit()
    db.refresh(message)

    other_user = get_other_user(chat, current_user)
    broadcast_socket_event_to_users(
        [current_user.id, other_user.id],
        socket_event(EVENT_MESSAGE_UPDATED, build_message_event_data(message)),
    )

    return message


def add_message_reaction(chat_id: int, message_id: int, data: ReactionCreateSchema, db: Session, current_user: User):
    chat = get_chat_or_404(chat_id, db)
    check_chat_member(chat, current_user)
    message = get_message_or_404(message_id, db)

    if message.chat_id != chat.id:
        raise HTTPException(status_code=404, detail="Message not found in this chat")

    reaction = db.query(MessageReaction).filter(
        MessageReaction.message_id == message.id,
        MessageReaction.user_id == current_user.id,
    ).first()

    if reaction:
        reaction.emoji = data.emoji
    else:
        reaction = MessageReaction(
            message_id=message.id,
            user_id=current_user.id,
            emoji=data.emoji,
        )
        db.add(reaction)

    db.commit()
    db.refresh(message)

    if message.sender_id != current_user.id:
        create_notification(db, message.sender_id, current_user.id, "reaction", message.id, "message")

    other_user = get_other_user(chat, current_user)
    broadcast_socket_event_to_users(
        [current_user.id, other_user.id],
        socket_event(EVENT_REACTION_CREATED, {
            "message_id": message.id,
            "chat_id": chat.id,
            "user_id": current_user.id,
            "emoji": data.emoji,
            "entity_type": "message",
        }),
    )

    return message

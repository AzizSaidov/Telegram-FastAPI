import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from groups.models import Group, GroupMember, GroupMessage, GroupMessageReaction, GroupReadState
from groups.permissions import GROUP_ADMIN, GROUP_MEMBER, check_group_admin, check_group_block, check_group_member, get_group_member
from groups.schemas import GroupCreateSchema, GroupMemberCreateSchema, GroupMessageUpdateSchema, GroupReactionCreateSchema, GroupUpdateSchema
from notifications.views import create_notification
from profiles.models import Profile
from sockets.schemas import EVENT_GROUP_MESSAGE_CREATED, EVENT_MESSAGE_DELETED, EVENT_MESSAGE_UPDATED, EVENT_REACTION_CREATED, socket_event
from sockets.utils import broadcast_socket_event_to_users
from users.models import User


GROUP_AVATARS_DIR = Path("media") / "groups" / "avatars"
GROUP_PHOTOS_DIR = Path("media") / "groups" / "photos"
GROUP_VIDEOS_DIR = Path("media") / "groups" / "videos"


def get_group_user_ids(group_id: int, db: Session):
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()

    return [member.user_id for member in members]


def build_group_message_event_data(message: GroupMessage):
    return {
        "id": message.id,
        "group_id": message.group_id,
        "sender_id": message.sender_id,
        "text": message.text,
        "media_url": message.media_url,
        "reply_to_id": message.reply_to_id,
        "forwarded_from_id": message.forwarded_from_id,
        "is_edited": message.is_edited,
        "is_pinned": message.is_pinned,
        "created_at": message.created_at.isoformat(),
    }


def save_group_avatar(avatar: UploadFile):
    if avatar.content_type is None or not avatar.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Group avatar must be an image")

    GROUP_AVATARS_DIR.mkdir(parents=True, exist_ok=True)

    allowed_suffixes = [".jpg", ".jpeg", ".png", ".webp"]
    file_suffix = Path(avatar.filename or "").suffix.lower()

    if file_suffix not in allowed_suffixes:
        file_suffix = ".jpg"

    file_name = f"{uuid4().hex}{file_suffix}"
    file_path = GROUP_AVATARS_DIR / file_name

    with file_path.open("wb") as file:
        shutil.copyfileobj(avatar.file, file)

    return f"/media/groups/avatars/{file_name}"


def save_group_media(media: UploadFile):
    if media.content_type is None:
        raise HTTPException(status_code=400, detail="Media file is required")

    if media.content_type.startswith("image/"):
        media_type = "photos"
        media_dir = GROUP_PHOTOS_DIR
        allowed_suffixes = [".jpg", ".jpeg", ".png", ".webp"]
        default_suffix = ".jpg"
    elif media.content_type.startswith("video/"):
        media_type = "videos"
        media_dir = GROUP_VIDEOS_DIR
        allowed_suffixes = [".mp4", ".mov", ".webm"]
        default_suffix = ".mp4"
    else:
        raise HTTPException(status_code=400, detail="Group message media must be photo or video")

    media_dir.mkdir(parents=True, exist_ok=True)

    file_suffix = Path(media.filename or "").suffix.lower()

    if file_suffix not in allowed_suffixes:
        file_suffix = default_suffix

    file_name = f"{uuid4().hex}{file_suffix}"
    file_path = media_dir / file_name

    with file_path.open("wb") as file:
        shutil.copyfileobj(media.file, file)

    return f"/media/groups/{media_type}/{file_name}"


def get_group_or_404(group_id: int, db: Session):
    group = db.query(Group).filter(Group.id == group_id).first()

    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    return group


def get_group_message_or_404(message_id: int, db: Session):
    message = db.query(GroupMessage).filter(GroupMessage.id == message_id).first()

    if message is None:
        raise HTTPException(status_code=404, detail="Group message not found")

    return message


def get_user_by_username(username: str, db: Session):
    profile = db.query(Profile).filter(Profile.username == username).first()

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    user = db.query(User).filter(User.id == profile.user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def get_group_unread_count(group_id: int, current_user: User, db: Session):
    read_state = db.query(GroupReadState).filter(
        GroupReadState.group_id == group_id,
        GroupReadState.user_id == current_user.id,
    ).first()

    unread_query = db.query(GroupMessage).filter(
        GroupMessage.group_id == group_id,
        GroupMessage.sender_id != current_user.id,
    )

    if read_state and read_state.last_read_message_id:
        unread_query = unread_query.filter(GroupMessage.id > read_state.last_read_message_id)

    return unread_query.count()


def build_group_response(group: Group, current_user: User, db: Session):
    current_member = get_group_member(group.id, current_user.id, db)
    last_message = db.query(GroupMessage).filter(GroupMessage.group_id == group.id).order_by(GroupMessage.created_at.desc()).first()
    members_count = db.query(GroupMember).filter(GroupMember.group_id == group.id).count()

    return {
        "id": group.id,
        "name": group.name,
        "avatar_url": group.avatar_url,
        "description": group.description,
        "created_at": group.created_at,
        "owner": group.owner,
        "current_user_role": current_member.role if current_member else GROUP_MEMBER,
        "members_count": members_count,
        "last_message": last_message,
        "unread_count": get_group_unread_count(group.id, current_user, db),
    }


def build_group_detail_response(group: Group, current_user: User, db: Session):
    data = build_group_response(group, current_user, db)
    data["members"] = db.query(GroupMember).filter(GroupMember.group_id == group.id).order_by(GroupMember.joined_at.asc()).all()

    return data


def get_groups(db: Session, current_user: User):
    memberships = db.query(GroupMember).filter(GroupMember.user_id == current_user.id).all()

    return sorted(
        [build_group_response(membership.group, current_user, db) for membership in memberships],
        key=lambda group: group["last_message"].created_at if group["last_message"] else group["created_at"],
        reverse=True,
    )


def create_group(data: GroupCreateSchema, avatar: UploadFile | None, db: Session, current_user: User):
    avatar_url = save_group_avatar(avatar) if avatar is not None else None

    new_group = Group(
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
        avatar_url=avatar_url,
    )

    db.add(new_group)
    db.flush()

    owner_member = GroupMember(
        group_id=new_group.id,
        user_id=current_user.id,
        role=GROUP_ADMIN,
    )

    db.add(owner_member)
    db.commit()
    db.refresh(new_group)

    return build_group_detail_response(new_group, current_user, db)


def get_group_detail(group_id: int, db: Session, current_user: User):
    group = get_group_or_404(group_id, db)
    check_group_member(group, current_user, db)

    return build_group_detail_response(group, current_user, db)


def update_group(group_id: int, data: GroupUpdateSchema, avatar: UploadFile | None, db: Session, current_user: User):
    group = get_group_or_404(group_id, db)
    check_group_admin(group, current_user, db)

    if data.name is not None:
        group.name = data.name

    if data.description is not None:
        group.description = data.description

    if avatar is not None:
        group.avatar_url = save_group_avatar(avatar)

    db.commit()
    db.refresh(group)

    return build_group_detail_response(group, current_user, db)


def get_group_members_count(group_id: int, db: Session, current_user: User):
    group = get_group_or_404(group_id, db)
    check_group_member(group, current_user, db)

    count = db.query(GroupMember).filter(GroupMember.group_id == group.id).count()

    return {"count": count}


def get_group_members(group_id: int, db: Session, current_user: User):
    group = get_group_or_404(group_id, db)
    check_group_member(group, current_user, db)

    return db.query(GroupMember).filter(GroupMember.group_id == group.id).order_by(GroupMember.joined_at.asc()).all()


def add_group_member(group_id: int, data: GroupMemberCreateSchema, db: Session, current_user: User):
    group = get_group_or_404(group_id, db)
    check_group_admin(group, current_user, db)
    user = get_user_by_username(data.username, db)

    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="You are already a group member")

    check_group_block(db, current_user.id, user.id)

    existing_member = get_group_member(group.id, user.id, db)

    if existing_member:
        raise HTTPException(status_code=400, detail="User already in group")

    new_member = GroupMember(
        group_id=group.id,
        user_id=user.id,
        role=GROUP_MEMBER,
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return new_member


def remove_group_member(group_id: int, username: str, db: Session, current_user: User):
    group = get_group_or_404(group_id, db)
    check_group_admin(group, current_user, db)
    user = get_user_by_username(username.strip().lower(), db)

    if user.id == group.owner_id:
        raise HTTPException(status_code=400, detail="Group owner cannot be removed")

    member = get_group_member(group.id, user.id, db)

    if member is None:
        raise HTTPException(status_code=404, detail="Group member not found")

    db.delete(member)
    db.commit()

    return {"detail": "Group member removed successfully"}


def make_group_admin(group_id: int, username: str, db: Session, current_user: User):
    group = get_group_or_404(group_id, db)
    check_group_admin(group, current_user, db)
    user = get_user_by_username(username.strip().lower(), db)
    member = get_group_member(group.id, user.id, db)

    if member is None:
        raise HTTPException(status_code=404, detail="Group member not found")

    member.role = GROUP_ADMIN

    db.commit()
    db.refresh(member)

    return member


def update_group_read_state(group: Group, current_user: User, db: Session):
    latest_message = db.query(GroupMessage).filter(GroupMessage.group_id == group.id).order_by(GroupMessage.id.desc()).first()

    if latest_message is None:
        return None

    read_state = db.query(GroupReadState).filter(
        GroupReadState.group_id == group.id,
        GroupReadState.user_id == current_user.id,
    ).first()

    if read_state is None:
        read_state = GroupReadState(
            group_id=group.id,
            user_id=current_user.id,
            last_read_message_id=latest_message.id,
        )
        db.add(read_state)
    else:
        read_state.last_read_message_id = latest_message.id

    db.commit()

    return read_state


def get_group_messages(group_id: int, db: Session, current_user: User):
    group = get_group_or_404(group_id, db)
    check_group_member(group, current_user, db)
    messages = db.query(GroupMessage).filter(GroupMessage.group_id == group.id).order_by(GroupMessage.created_at.asc()).all()

    update_group_read_state(group, current_user, db)

    return messages


def send_group_message(
    group_id: int,
    text: str | None,
    reply_to_id: int | None,
    forwarded_from_id: int | None,
    media: UploadFile | None,
    db: Session,
    current_user: User,
):
    group = get_group_or_404(group_id, db)
    check_group_member(group, current_user, db)

    message_text = text.strip() if text is not None else None
    media_url = save_group_media(media) if media is not None else None
    forwarded_from = None

    if reply_to_id is not None:
        reply_to = get_group_message_or_404(reply_to_id, db)

        if reply_to.group_id != group.id:
            raise HTTPException(status_code=400, detail="Reply message is not from this group")

    if forwarded_from_id is not None:
        forwarded_from = get_group_message_or_404(forwarded_from_id, db)

        if message_text is None and media_url is None:
            message_text = forwarded_from.text
            media_url = forwarded_from.media_url

    if not message_text and media_url is None:
        raise HTTPException(status_code=400, detail="Message text or media is required")

    new_message = GroupMessage(
        group_id=group.id,
        sender_id=current_user.id,
        text=message_text,
        media_url=media_url,
        reply_to_id=reply_to_id,
        forwarded_from_id=forwarded_from.id if forwarded_from else None,
    )

    db.add(new_message)
    db.commit()
    db.refresh(new_message)

    user_ids = get_group_user_ids(group.id, db)

    for user_id in user_ids:
        create_notification(db, user_id, current_user.id, "group_message", new_message.id, "group_message")

    broadcast_socket_event_to_users(
        user_ids,
        socket_event(EVENT_GROUP_MESSAGE_CREATED, build_group_message_event_data(new_message)),
    )

    return new_message


def edit_group_message(group_id: int, message_id: int, data: GroupMessageUpdateSchema, db: Session, current_user: User):
    group = get_group_or_404(group_id, db)
    check_group_member(group, current_user, db)
    message = get_group_message_or_404(message_id, db)

    if message.group_id != group.id:
        raise HTTPException(status_code=404, detail="Group message not found in this group")

    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can edit only your own message")

    message.text = data.text
    message.is_edited = True

    db.commit()
    db.refresh(message)

    broadcast_socket_event_to_users(
        get_group_user_ids(group.id, db),
        socket_event(EVENT_MESSAGE_UPDATED, build_group_message_event_data(message)),
    )

    return message


def delete_group_message(group_id: int, message_id: int, db: Session, current_user: User):
    group = get_group_or_404(group_id, db)
    member = check_group_member(group, current_user, db)
    message = get_group_message_or_404(message_id, db)

    if message.group_id != group.id:
        raise HTTPException(status_code=404, detail="Group message not found in this group")

    if message.sender_id != current_user.id and member.role != GROUP_ADMIN:
        raise HTTPException(status_code=403, detail="You can delete only your own message")

    event_data = {
        "id": message.id,
        "group_id": group.id,
    }
    user_ids = get_group_user_ids(group.id, db)

    db.query(GroupReadState).filter(GroupReadState.last_read_message_id == message.id).update({"last_read_message_id": None})
    db.query(GroupMessage).filter(GroupMessage.reply_to_id == message.id).update({"reply_to_id": None})
    db.query(GroupMessage).filter(GroupMessage.forwarded_from_id == message.id).update({"forwarded_from_id": None})
    db.query(GroupMessageReaction).filter(GroupMessageReaction.message_id == message.id).delete()
    db.delete(message)
    db.commit()

    broadcast_socket_event_to_users(
        user_ids,
        socket_event(EVENT_MESSAGE_DELETED, event_data),
    )

    return {"detail": "Group message deleted successfully"}


def pin_group_message(group_id: int, message_id: int, db: Session, current_user: User):
    group = get_group_or_404(group_id, db)
    check_group_admin(group, current_user, db)
    message = get_group_message_or_404(message_id, db)

    if message.group_id != group.id:
        raise HTTPException(status_code=404, detail="Group message not found in this group")

    db.query(GroupMessage).filter(
        GroupMessage.group_id == group.id,
        GroupMessage.is_pinned == True,
    ).update({"is_pinned": False})

    message.is_pinned = True

    db.commit()
    db.refresh(message)

    broadcast_socket_event_to_users(
        get_group_user_ids(group.id, db),
        socket_event(EVENT_MESSAGE_UPDATED, build_group_message_event_data(message)),
    )

    return message


def add_group_message_reaction(group_id: int, message_id: int, data: GroupReactionCreateSchema, db: Session, current_user: User):
    group = get_group_or_404(group_id, db)
    check_group_member(group, current_user, db)
    message = get_group_message_or_404(message_id, db)

    if message.group_id != group.id:
        raise HTTPException(status_code=404, detail="Group message not found in this group")

    reaction = db.query(GroupMessageReaction).filter(
        GroupMessageReaction.message_id == message.id,
        GroupMessageReaction.user_id == current_user.id,
    ).first()

    if reaction:
        reaction.emoji = data.emoji
    else:
        reaction = GroupMessageReaction(
            message_id=message.id,
            user_id=current_user.id,
            emoji=data.emoji,
        )
        db.add(reaction)

    db.commit()
    db.refresh(message)

    if message.sender_id != current_user.id:
        create_notification(db, message.sender_id, current_user.id, "reaction", message.id, "group_message")

    broadcast_socket_event_to_users(
        get_group_user_ids(group.id, db),
        socket_event(EVENT_REACTION_CREATED, {
            "message_id": message.id,
            "group_id": group.id,
            "user_id": current_user.id,
            "emoji": data.emoji,
            "entity_type": "group_message",
        }),
    )

    return message

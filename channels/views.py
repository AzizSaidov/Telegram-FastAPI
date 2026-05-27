import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from channels.models import Channel, ChannelMember, ChannelPost, ChannelPostReaction, ChannelReadState
from channels.permissions import CHANNEL_ADMIN, CHANNEL_SUBSCRIBER, check_channel_admin, check_channel_member, check_channel_visible, get_channel_member
from channels.schemas import ChannelCreateSchema, ChannelMemberCreateSchema, ChannelPostUpdateSchema, ChannelReactionCreateSchema, ChannelUpdateSchema
from profiles.models import Profile
from users.models import User


CHANNEL_AVATARS_DIR = Path("media") / "channels" / "avatars"
CHANNEL_PHOTOS_DIR = Path("media") / "channels" / "photos"
CHANNEL_VIDEOS_DIR = Path("media") / "channels" / "videos"


def save_channel_avatar(avatar: UploadFile):
    if avatar.content_type is None or not avatar.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Channel avatar must be an image")

    CHANNEL_AVATARS_DIR.mkdir(parents=True, exist_ok=True)

    allowed_suffixes = [".jpg", ".jpeg", ".png", ".webp"]
    file_suffix = Path(avatar.filename or "").suffix.lower()

    if file_suffix not in allowed_suffixes:
        file_suffix = ".jpg"

    file_name = f"{uuid4().hex}{file_suffix}"
    file_path = CHANNEL_AVATARS_DIR / file_name

    with file_path.open("wb") as file:
        shutil.copyfileobj(avatar.file, file)

    return f"/media/channels/avatars/{file_name}"


def save_channel_media(media: UploadFile):
    if media.content_type is None:
        raise HTTPException(status_code=400, detail="Media file is required")

    if media.content_type.startswith("image/"):
        media_type = "photos"
        media_dir = CHANNEL_PHOTOS_DIR
        allowed_suffixes = [".jpg", ".jpeg", ".png", ".webp"]
        default_suffix = ".jpg"
    elif media.content_type.startswith("video/"):
        media_type = "videos"
        media_dir = CHANNEL_VIDEOS_DIR
        allowed_suffixes = [".mp4", ".mov", ".webm"]
        default_suffix = ".mp4"
    else:
        raise HTTPException(status_code=400, detail="Channel post media must be photo or video")

    media_dir.mkdir(parents=True, exist_ok=True)

    file_suffix = Path(media.filename or "").suffix.lower()

    if file_suffix not in allowed_suffixes:
        file_suffix = default_suffix

    file_name = f"{uuid4().hex}{file_suffix}"
    file_path = media_dir / file_name

    with file_path.open("wb") as file:
        shutil.copyfileobj(media.file, file)

    return f"/media/channels/{media_type}/{file_name}"


def get_channel_or_404(channel_id: int, db: Session):
    channel = db.query(Channel).filter(Channel.id == channel_id).first()

    if channel is None:
        raise HTTPException(status_code=404, detail="Channel not found")

    return channel


def get_channel_post_or_404(post_id: int, db: Session):
    post = db.query(ChannelPost).filter(ChannelPost.id == post_id).first()

    if post is None:
        raise HTTPException(status_code=404, detail="Channel post not found")

    return post


def get_user_by_username(username: str, db: Session):
    profile = db.query(Profile).filter(Profile.username == username).first()

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    user = db.query(User).filter(User.id == profile.user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def get_channel_unread_count(channel_id: int, current_user: User, db: Session):
    member = get_channel_member(channel_id, current_user.id, db)

    if member is None:
        return 0

    read_state = db.query(ChannelReadState).filter(
        ChannelReadState.channel_id == channel_id,
        ChannelReadState.user_id == current_user.id,
    ).first()

    unread_query = db.query(ChannelPost).filter(
        ChannelPost.channel_id == channel_id,
        ChannelPost.sender_id != current_user.id,
    )

    if read_state and read_state.last_read_post_id:
        unread_query = unread_query.filter(ChannelPost.id > read_state.last_read_post_id)

    return unread_query.count()


def build_channel_response(channel: Channel, current_user: User, db: Session):
    current_member = get_channel_member(channel.id, current_user.id, db)
    last_post = db.query(ChannelPost).filter(ChannelPost.channel_id == channel.id).order_by(ChannelPost.created_at.desc()).first()
    members_count = db.query(ChannelMember).filter(ChannelMember.channel_id == channel.id).count()

    return {
        "id": channel.id,
        "name": channel.name,
        "avatar_url": channel.avatar_url,
        "description": channel.description,
        "is_public": channel.is_public,
        "created_at": channel.created_at,
        "owner": channel.owner,
        "current_user_role": current_member.role if current_member else None,
        "members_count": members_count,
        "last_post": last_post,
        "unread_count": get_channel_unread_count(channel.id, current_user, db),
    }


def build_channel_detail_response(channel: Channel, current_user: User, db: Session):
    data = build_channel_response(channel, current_user, db)
    data["members"] = db.query(ChannelMember).filter(ChannelMember.channel_id == channel.id).order_by(ChannelMember.joined_at.asc()).all()

    return data


def build_channel_post_response(post: ChannelPost, current_user: User, db: Session):
    poll = None

    if post.poll:
        from polls.views import build_poll_response

        poll = build_poll_response(post.poll, current_user, db)

    return {
        "id": post.id,
        "text": post.text,
        "media_url": post.media_url,
        "is_edited": post.is_edited,
        "is_pinned": post.is_pinned,
        "created_at": post.created_at,
        "sender": post.sender,
        "reactions": post.reactions,
        "poll": poll,
    }


def get_channels(db: Session, current_user: User):
    memberships = db.query(ChannelMember).filter(ChannelMember.user_id == current_user.id).all()

    return sorted(
        [build_channel_response(membership.channel, current_user, db) for membership in memberships],
        key=lambda channel: channel["last_post"].created_at if channel["last_post"] else channel["created_at"],
        reverse=True,
    )


def create_channel(data: ChannelCreateSchema, avatar: UploadFile | None, db: Session, current_user: User):
    avatar_url = save_channel_avatar(avatar) if avatar is not None else None

    new_channel = Channel(
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
        is_public=data.is_public,
        avatar_url=avatar_url,
    )

    db.add(new_channel)
    db.flush()

    owner_member = ChannelMember(
        channel_id=new_channel.id,
        user_id=current_user.id,
        role=CHANNEL_ADMIN,
    )

    db.add(owner_member)
    db.commit()
    db.refresh(new_channel)

    return build_channel_detail_response(new_channel, current_user, db)


def get_channel_detail(channel_id: int, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_visible(channel, current_user, db)

    return build_channel_detail_response(channel, current_user, db)


def update_channel(channel_id: int, data: ChannelUpdateSchema, avatar: UploadFile | None, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_admin(channel, current_user, db)

    if data.name is not None:
        channel.name = data.name

    if data.description is not None:
        channel.description = data.description

    if data.is_public is not None:
        channel.is_public = data.is_public

    if avatar is not None:
        channel.avatar_url = save_channel_avatar(avatar)

    db.commit()
    db.refresh(channel)

    return build_channel_detail_response(channel, current_user, db)


def get_channel_members_count(channel_id: int, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_visible(channel, current_user, db)

    count = db.query(ChannelMember).filter(ChannelMember.channel_id == channel.id).count()

    return {"count": count}


def get_channel_members(channel_id: int, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_member(channel, current_user, db)

    return db.query(ChannelMember).filter(ChannelMember.channel_id == channel.id).order_by(ChannelMember.joined_at.asc()).all()


def add_channel_member(channel_id: int, data: ChannelMemberCreateSchema, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_admin(channel, current_user, db)
    user = get_user_by_username(data.username, db)

    existing_member = get_channel_member(channel.id, user.id, db)

    if existing_member:
        raise HTTPException(status_code=400, detail="User already in channel")

    new_member = ChannelMember(
        channel_id=channel.id,
        user_id=user.id,
        role=CHANNEL_SUBSCRIBER,
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return new_member


def remove_channel_member(channel_id: int, username: str, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_admin(channel, current_user, db)
    user = get_user_by_username(username.strip().lower(), db)

    if user.id == channel.owner_id:
        raise HTTPException(status_code=400, detail="Channel owner cannot be removed")

    member = get_channel_member(channel.id, user.id, db)

    if member is None:
        raise HTTPException(status_code=404, detail="Channel member not found")

    db.query(ChannelReadState).filter(
        ChannelReadState.channel_id == channel.id,
        ChannelReadState.user_id == user.id,
    ).delete()
    db.delete(member)
    db.commit()

    return {"detail": "Channel member removed successfully"}


def make_channel_admin(channel_id: int, username: str, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_admin(channel, current_user, db)
    user = get_user_by_username(username.strip().lower(), db)
    member = get_channel_member(channel.id, user.id, db)

    if member is None:
        raise HTTPException(status_code=404, detail="Channel member not found")

    member.role = CHANNEL_ADMIN

    db.commit()
    db.refresh(member)

    return member


def subscribe_channel(channel_id: int, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)

    if not channel.is_public:
        raise HTTPException(status_code=403, detail="You cannot subscribe to private channel")

    existing_member = get_channel_member(channel.id, current_user.id, db)

    if existing_member:
        raise HTTPException(status_code=400, detail="You are already subscribed")

    new_member = ChannelMember(
        channel_id=channel.id,
        user_id=current_user.id,
        role=CHANNEL_SUBSCRIBER,
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return new_member


def unsubscribe_channel(channel_id: int, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)

    if channel.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="Channel owner cannot unsubscribe")

    member = get_channel_member(channel.id, current_user.id, db)

    if member is None:
        raise HTTPException(status_code=404, detail="Channel member not found")

    db.query(ChannelReadState).filter(
        ChannelReadState.channel_id == channel.id,
        ChannelReadState.user_id == current_user.id,
    ).delete()
    db.delete(member)
    db.commit()

    return {"detail": "Unsubscribed successfully"}


def update_channel_read_state(channel: Channel, current_user: User, db: Session):
    member = get_channel_member(channel.id, current_user.id, db)

    if member is None:
        return None

    latest_post = db.query(ChannelPost).filter(ChannelPost.channel_id == channel.id).order_by(ChannelPost.id.desc()).first()

    if latest_post is None:
        return None

    read_state = db.query(ChannelReadState).filter(
        ChannelReadState.channel_id == channel.id,
        ChannelReadState.user_id == current_user.id,
    ).first()

    if read_state is None:
        read_state = ChannelReadState(
            channel_id=channel.id,
            user_id=current_user.id,
            last_read_post_id=latest_post.id,
        )
        db.add(read_state)
    else:
        read_state.last_read_post_id = latest_post.id

    db.commit()

    return read_state


def get_channel_posts(channel_id: int, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_visible(channel, current_user, db)
    posts = db.query(ChannelPost).filter(ChannelPost.channel_id == channel.id).order_by(ChannelPost.created_at.asc()).all()

    update_channel_read_state(channel, current_user, db)

    return [build_channel_post_response(post, current_user, db) for post in posts]


def create_channel_post(channel_id: int, text: str | None, media: UploadFile | None, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_admin(channel, current_user, db)

    post_text = text.strip() if text is not None else None
    media_url = save_channel_media(media) if media is not None else None

    if not post_text and media_url is None:
        raise HTTPException(status_code=400, detail="Post text or media is required")

    new_post = ChannelPost(
        channel_id=channel.id,
        sender_id=current_user.id,
        text=post_text,
        media_url=media_url,
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return build_channel_post_response(new_post, current_user, db)


def edit_channel_post(channel_id: int, post_id: int, data: ChannelPostUpdateSchema, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_admin(channel, current_user, db)
    post = get_channel_post_or_404(post_id, db)

    if post.channel_id != channel.id:
        raise HTTPException(status_code=404, detail="Channel post not found in this channel")

    post.text = data.text
    post.is_edited = True

    db.commit()
    db.refresh(post)

    return build_channel_post_response(post, current_user, db)


def delete_channel_post(channel_id: int, post_id: int, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_admin(channel, current_user, db)
    post = get_channel_post_or_404(post_id, db)

    if post.channel_id != channel.id:
        raise HTTPException(status_code=404, detail="Channel post not found in this channel")

    db.query(ChannelReadState).filter(ChannelReadState.last_read_post_id == post.id).update({"last_read_post_id": None})
    db.query(ChannelPostReaction).filter(ChannelPostReaction.post_id == post.id).delete()
    db.delete(post)
    db.commit()

    return {"detail": "Channel post deleted successfully"}


def pin_channel_post(channel_id: int, post_id: int, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_admin(channel, current_user, db)
    post = get_channel_post_or_404(post_id, db)

    if post.channel_id != channel.id:
        raise HTTPException(status_code=404, detail="Channel post not found in this channel")

    db.query(ChannelPost).filter(
        ChannelPost.channel_id == channel.id,
        ChannelPost.is_pinned == True,
    ).update({"is_pinned": False})

    post.is_pinned = True

    db.commit()
    db.refresh(post)

    return build_channel_post_response(post, current_user, db)


def add_channel_post_reaction(channel_id: int, post_id: int, data: ChannelReactionCreateSchema, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_member(channel, current_user, db)
    post = get_channel_post_or_404(post_id, db)

    if post.channel_id != channel.id:
        raise HTTPException(status_code=404, detail="Channel post not found in this channel")

    reaction = db.query(ChannelPostReaction).filter(
        ChannelPostReaction.post_id == post.id,
        ChannelPostReaction.user_id == current_user.id,
    ).first()

    if reaction:
        reaction.emoji = data.emoji
    else:
        reaction = ChannelPostReaction(
            post_id=post.id,
            user_id=current_user.id,
            emoji=data.emoji,
        )
        db.add(reaction)

    db.commit()
    db.refresh(post)

    return build_channel_post_response(post, current_user, db)

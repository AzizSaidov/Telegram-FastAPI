import shutil
from datetime import timedelta, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from blocks.models import BlockedUser
from chats.models import Chat
from contacts.models import Contact
from stories.models import Story, StoryView
from users.models import User
from utils import get_dushanbe_time


STORIES_PHOTOS_DIR = Path("media") / "stories" / "photos"
STORIES_VIDEOS_DIR = Path("media") / "stories" / "videos"


def save_story_media(media: UploadFile):
    if media.content_type is None:
        raise HTTPException(status_code=400, detail="Media file is required")

    if media.content_type.startswith("image/"):
        media_type = "photo"
        media_dir = STORIES_PHOTOS_DIR
        allowed_suffixes = [".jpg", ".jpeg", ".png", ".webp"]
        default_suffix = ".jpg"
    elif media.content_type.startswith("video/"):
        media_type = "video"
        media_dir = STORIES_VIDEOS_DIR
        allowed_suffixes = [".mp4", ".mov", ".webm"]
        default_suffix = ".mp4"
    else:
        raise HTTPException(status_code=400, detail="Story media must be photo or video")

    media_dir.mkdir(parents=True, exist_ok=True)

    file_suffix = Path(media.filename or "").suffix.lower()

    if file_suffix not in allowed_suffixes:
        file_suffix = default_suffix

    file_name = f"{uuid4().hex}{file_suffix}"
    file_path = media_dir / file_name

    with file_path.open("wb") as file:
        shutil.copyfileobj(media.file, file)

    return f"/media/stories/{media_type}s/{file_name}", media_type


def create_story(media: UploadFile, db: Session, current_user: User):
    media_url, media_type = save_story_media(media)

    new_story = Story(
        user_id=current_user.id,
        media_url=media_url,
        media_type=media_type,
        expires_at=get_dushanbe_time() + timedelta(hours=24),
    )

    db.add(new_story)
    db.commit()
    db.refresh(new_story)

    return new_story


def get_active_stories(db: Session, current_user: User, limit: int, offset: int):
    now = get_dushanbe_time()

    # Users the current user has a private chat with
    chats = db.query(Chat).filter(
        (Chat.user_id_1 == current_user.id) | (Chat.user_id_2 == current_user.id)
    ).all()
    chat_partner_ids = {
        (c.user_id_2 if c.user_id_1 == current_user.id else c.user_id_1)
        for c in chats
    }

    # Users in contacts
    contact_ids = {
        c.contact_id
        for c in db.query(Contact.contact_id).filter(Contact.owner_id == current_user.id).all()
    }

    # Visible = own + chat partners + contacts
    visible_ids = chat_partner_ids | contact_ids | {current_user.id}

    # Blocked users
    blocked_me = db.query(BlockedUser.blocker_id).filter(BlockedUser.blocked_id == current_user.id).all()
    blocked_by_me = db.query(BlockedUser.blocked_id).filter(BlockedUser.blocker_id == current_user.id).all()
    blocked_user_ids = {b.blocker_id for b in blocked_me} | {b.blocked_id for b in blocked_by_me}

    visible_ids -= blocked_user_ids

    stories_query = db.query(Story).filter(
        Story.expires_at > now,
        Story.user_id.in_(visible_ids),
    )

    stories = stories_query.order_by(Story.created_at.desc()).offset(offset).limit(limit).all()

    story_ids = [story.id for story in stories]
    viewed_story_ids = set()
    view_counts = {}

    if story_ids:
        viewed_story_ids = {
            row.story_id
            for row in db.query(StoryView.story_id).filter(
                StoryView.user_id == current_user.id,
                StoryView.story_id.in_(story_ids),
            ).all()
        }
        view_counts = {
            story_id: count
            for story_id, count in db.query(
                StoryView.story_id,
                func.count(StoryView.id),
            ).join(
                Story,
                Story.id == StoryView.story_id,
            ).filter(
                StoryView.story_id.in_(story_ids),
                StoryView.user_id != Story.user_id,
            ).group_by(StoryView.story_id).all()
        }

    grouped_stories = {}

    for story in stories:
        is_me = story.user_id == current_user.id
        is_viewed = is_me or story.id in viewed_story_ids

        if story.user_id not in grouped_stories:
            grouped_stories[story.user_id] = {
                "user": story.user,
                "stories": [],
                "is_me": is_me,
                "has_unviewed": False,
                "last_story_at": story.created_at,
            }

        grouped_stories[story.user_id]["stories"].append({
            "id": story.id,
            "media_url": story.media_url,
            "media_type": story.media_type,
            "expires_at": story.expires_at,
            "created_at": story.created_at,
            "is_viewed_by_me": is_viewed,
            "views_count": view_counts.get(story.id, 0),
        })

        if not is_me and not is_viewed:
            grouped_stories[story.user_id]["has_unviewed"] = True

    groups = list(grouped_stories.values())

    for group in groups:
        group["stories"].sort(key=lambda item: item["created_at"])

    groups.sort(
        key=lambda group: (
            not group["is_me"],
            not group["has_unviewed"] if not group["is_me"] else True,
            -(group["last_story_at"].timestamp() if group["last_story_at"] else 0),
        )
    )

    return groups


def view_story(story_id: int, db: Session, current_user: User):
    story = db.query(Story).filter(Story.id == story_id).first()

    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")

    expires_at = story.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= get_dushanbe_time():
        raise HTTPException(status_code=400, detail="Story expired")

    if story.user_id == current_user.id:
        return {"detail": "Own story opened"}

    blocked = db.query(BlockedUser).filter(
        (
            (BlockedUser.blocker_id == story.user_id)
            & (BlockedUser.blocked_id == current_user.id)
        )
        | (
            (BlockedUser.blocker_id == current_user.id)
            & (BlockedUser.blocked_id == story.user_id)
        ),
    ).first()

    if blocked:
        raise HTTPException(status_code=403, detail="You cannot view this story")

    existing_view = db.query(StoryView).filter(
        StoryView.story_id == story.id,
        StoryView.user_id == current_user.id,
    ).first()

    if existing_view:
        return {"detail": "Story already viewed"}

    new_view = StoryView(
        story_id=story.id,
        user_id=current_user.id,
    )

    db.add(new_view)
    db.commit()

    return {"detail": "Story viewed successfully"}


def get_story_views(story_id: int, db: Session, current_user: User):
    story = db.query(Story).filter(Story.id == story_id).first()

    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")

    if story.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can see views only for your story")

    return db.query(StoryView).filter(StoryView.story_id == story.id).all()

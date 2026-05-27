import shutil
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from blocks.models import BlockedUser
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


def get_active_stories(db: Session, current_user: User):
    now = get_dushanbe_time()
    blocked_me = db.query(BlockedUser.blocker_id).filter(
        BlockedUser.blocked_id == current_user.id,
    ).all()
    blocked_by_me = db.query(BlockedUser.blocked_id).filter(
        BlockedUser.blocker_id == current_user.id,
    ).all()
    blocked_user_ids = [blocked_user.blocker_id for blocked_user in blocked_me]
    blocked_user_ids += [blocked_user.blocked_id for blocked_user in blocked_by_me]

    stories_query = db.query(Story).filter(Story.expires_at > now)

    if blocked_user_ids:
        stories_query = stories_query.filter(Story.user_id.notin_(blocked_user_ids))

    stories = stories_query.order_by(Story.created_at.desc()).all()
    grouped_stories = {}

    for story in stories:
        if story.user_id not in grouped_stories:
            grouped_stories[story.user_id] = {
                "user": story.user,
                "stories": [],
            }

        grouped_stories[story.user_id]["stories"].append(story)

    return list(grouped_stories.values())


def view_story(story_id: int, db: Session, current_user: User):
    story = db.query(Story).filter(Story.id == story_id).first()

    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")

    if story.expires_at <= get_dushanbe_time():
        raise HTTPException(status_code=400, detail="Story expired")

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

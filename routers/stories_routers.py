from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from stories.schemas import DetailResponse, StoryGroupRead, StoryRead, StoryViewRead
from stories.views import create_story, get_active_stories, get_story_views, view_story
from users.auth import get_current_user
from users.models import User


stories_router = APIRouter(prefix="/stories", tags=["Stories"])


@stories_router.get("/", response_model=list[StoryGroupRead])
def stories_list(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_active_stories(db, current_user, limit, offset)


@stories_router.post("/", response_model=StoryRead, status_code=201)
def create_new_story(
    media: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_story(media, db, current_user)


@stories_router.post("/view/{story_id}", response_model=DetailResponse)
def mark_story_as_viewed(story_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return view_story(story_id, db, current_user)


@stories_router.get("/{story_id}/views", response_model=list[StoryViewRead])
def story_views(story_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_story_views(story_id, db, current_user)

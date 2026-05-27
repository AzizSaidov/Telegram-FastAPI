from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from polls.schemas import PollCreateSchema, PollRead, PollVoteSchema
from polls.views import create_poll, get_poll_detail, vote_poll
from users.auth import get_current_user
from users.models import User


polls_router = APIRouter(tags=["Polls"])


@polls_router.post("/channels/{channel_id}/posts/{post_id}/polls", response_model=PollRead, status_code=201)
def create_channel_post_poll(
    channel_id: int,
    post_id: int,
    data: PollCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_poll(channel_id, post_id, data, db, current_user)


@polls_router.get("/polls/{poll_id}", response_model=PollRead)
def poll_detail(poll_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_poll_detail(poll_id, db, current_user)


@polls_router.post("/polls/{poll_id}/vote", response_model=PollRead)
def vote_for_poll(
    poll_id: int,
    data: PollVoteSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return vote_poll(poll_id, data, db, current_user)

from fastapi import HTTPException
from sqlalchemy.orm import Session

from channels.models import ChannelPost
from channels.permissions import check_channel_admin, check_channel_member, check_channel_visible
from channels.views import get_channel_or_404, get_channel_post_or_404
from polls.models import Poll, PollOption, PollVote
from polls.schemas import PollCreateSchema, PollVoteSchema
from users.models import User


def build_poll_response(poll: Poll, current_user: User, db: Session):
    total_votes = db.query(PollVote).filter(PollVote.poll_id == poll.id).count()
    my_vote = db.query(PollVote).filter(
        PollVote.poll_id == poll.id,
        PollVote.user_id == current_user.id,
    ).first()

    options = []

    for option in poll.options:
        votes_count = db.query(PollVote).filter(PollVote.option_id == option.id).count()
        percent = int((votes_count / total_votes) * 100) if total_votes else 0

        options.append({
            "id": option.id,
            "text": option.text,
            "votes_count": votes_count,
            "percent": percent,
            "is_voted_by_me": my_vote.option_id == option.id if my_vote else False,
        })

    return {
        "id": poll.id,
        "question": poll.question,
        "options": options,
        "total_votes": total_votes,
        "is_voted_by_me": my_vote is not None,
        "created_at": poll.created_at,
    }


def get_poll_or_404(poll_id: int, db: Session):
    poll = db.query(Poll).filter(Poll.id == poll_id).first()

    if poll is None:
        raise HTTPException(status_code=404, detail="Poll not found")

    return poll


def create_poll(channel_id: int, post_id: int, data: PollCreateSchema, db: Session, current_user: User):
    channel = get_channel_or_404(channel_id, db)
    check_channel_admin(channel, current_user, db)
    post = get_channel_post_or_404(post_id, db)

    if post.channel_id != channel.id:
        raise HTTPException(status_code=404, detail="Channel post not found in this channel")

    existing_poll = db.query(Poll).filter(Poll.channel_post_id == post.id).first()

    if existing_poll:
        raise HTTPException(status_code=400, detail="Poll already exists for this post")

    new_poll = Poll(
        channel_post_id=post.id,
        question=data.question,
    )

    db.add(new_poll)
    db.flush()

    for option in data.options:
        db.add(PollOption(
            poll_id=new_poll.id,
            text=option,
        ))

    db.commit()
    db.refresh(new_poll)

    return build_poll_response(new_poll, current_user, db)


def get_poll_detail(poll_id: int, db: Session, current_user: User):
    poll = get_poll_or_404(poll_id, db)
    post = db.query(ChannelPost).filter(ChannelPost.id == poll.channel_post_id).first()

    if post is None:
        raise HTTPException(status_code=404, detail="Channel post not found")

    check_channel_visible(post.channel, current_user, db)

    return build_poll_response(poll, current_user, db)


def vote_poll(poll_id: int, data: PollVoteSchema, db: Session, current_user: User):
    poll = get_poll_or_404(poll_id, db)
    post = db.query(ChannelPost).filter(ChannelPost.id == poll.channel_post_id).first()

    if post is None:
        raise HTTPException(status_code=404, detail="Channel post not found")

    check_channel_member(post.channel, current_user, db)

    option = db.query(PollOption).filter(
        PollOption.id == data.option_id,
        PollOption.poll_id == poll.id,
    ).first()

    if option is None:
        raise HTTPException(status_code=404, detail="Poll option not found")

    vote = db.query(PollVote).filter(
        PollVote.poll_id == poll.id,
        PollVote.user_id == current_user.id,
    ).first()

    if vote:
        vote.option_id = option.id
    else:
        vote = PollVote(
            poll_id=poll.id,
            option_id=option.id,
            user_id=current_user.id,
        )
        db.add(vote)

    db.commit()
    db.refresh(poll)

    return build_poll_response(poll, current_user, db)

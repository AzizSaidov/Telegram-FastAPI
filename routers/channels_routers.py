from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from channels.schemas import ChannelCreateSchema, ChannelDetailRead, ChannelMemberCreateSchema, ChannelMemberRead, ChannelPostRead, ChannelPostUpdateSchema, ChannelReactionCreateSchema, ChannelRead, ChannelUpdateSchema, DetailResponse, MembersCountRead
from channels.views import add_channel_member, add_channel_post_reaction, create_channel, create_channel_post, delete_channel_post, edit_channel_post, get_channel_detail, get_channel_members, get_channel_members_count, get_channel_posts, get_channels, make_channel_admin, pin_channel_post, remove_channel_member, search_channels, subscribe_channel, unsubscribe_channel, update_channel
from database import get_db
from users.auth import get_current_user
from users.models import User


channels_router = APIRouter(prefix="/channels", tags=["Channels"])


@channels_router.get("/", response_model=list[ChannelRead])
def channels_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_channels(db, current_user)


@channels_router.post("/", response_model=ChannelDetailRead, status_code=201)
def create_new_channel(
    name: str = Form(...),
    description: str | None = Form(None),
    is_public: bool = Form(True),
    avatar: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = ChannelCreateSchema(
        name=name,
        description=description,
        is_public=is_public,
    )

    return create_channel(data, avatar, db, current_user)


@channels_router.get("/search", response_model=list[ChannelRead])
def channels_search(q: str = Query(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return search_channels(q, db, current_user)


@channels_router.get("/{channel_id}", response_model=ChannelDetailRead)
def channel_detail(channel_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_channel_detail(channel_id, db, current_user)


@channels_router.put("/{channel_id}", response_model=ChannelDetailRead)
def update_channel_info(
    channel_id: int,
    name: str | None = Form(None),
    description: str | None = Form(None),
    is_public: bool | None = Form(None),
    avatar: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = ChannelUpdateSchema(
        name=name,
        description=description,
        is_public=is_public,
    )

    return update_channel(channel_id, data, avatar, db, current_user)


@channels_router.get("/{channel_id}/members/count", response_model=MembersCountRead)
def channel_members_count(channel_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_channel_members_count(channel_id, db, current_user)


@channels_router.get("/{channel_id}/members", response_model=list[ChannelMemberRead])
def channel_members(channel_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_channel_members(channel_id, db, current_user)


@channels_router.post("/{channel_id}/members", response_model=ChannelMemberRead, status_code=201)
def create_channel_member(
    channel_id: int,
    data: ChannelMemberCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return add_channel_member(channel_id, data, db, current_user)


@channels_router.delete("/{channel_id}/members/{username}", response_model=DetailResponse)
def delete_channel_member(channel_id: int, username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return remove_channel_member(channel_id, username, db, current_user)


@channels_router.post("/{channel_id}/members/{username}/admin", response_model=ChannelMemberRead)
def add_channel_admin(channel_id: int, username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return make_channel_admin(channel_id, username, db, current_user)


@channels_router.post("/{channel_id}/subscribe", response_model=ChannelMemberRead, status_code=201)
def subscribe_to_channel(channel_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return subscribe_channel(channel_id, db, current_user)


@channels_router.delete("/{channel_id}/subscribe", response_model=DetailResponse)
def unsubscribe_from_channel(channel_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return unsubscribe_channel(channel_id, db, current_user)


@channels_router.get("/{channel_id}/posts", response_model=list[ChannelPostRead])
def channel_posts(
    channel_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_channel_posts(channel_id, db, current_user, limit, offset)


@channels_router.post("/{channel_id}/posts", response_model=ChannelPostRead, status_code=201)
def create_new_channel_post(
    channel_id: int,
    text: str | None = Form(None),
    media: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_channel_post(channel_id, text, media, db, current_user)


@channels_router.put("/{channel_id}/posts/{post_id}", response_model=ChannelPostRead)
def update_channel_post(
    channel_id: int,
    post_id: int,
    data: ChannelPostUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return edit_channel_post(channel_id, post_id, data, db, current_user)


@channels_router.delete("/{channel_id}/posts/{post_id}", response_model=DetailResponse)
def remove_channel_post(channel_id: int, post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return delete_channel_post(channel_id, post_id, db, current_user)


@channels_router.post("/{channel_id}/posts/{post_id}/pin", response_model=ChannelPostRead)
def pin_post_in_channel(channel_id: int, post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return pin_channel_post(channel_id, post_id, db, current_user)


@channels_router.post("/{channel_id}/posts/{post_id}/reactions", response_model=ChannelPostRead)
def create_channel_post_reaction(
    channel_id: int,
    post_id: int,
    data: ChannelReactionCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return add_channel_post_reaction(channel_id, post_id, data, db, current_user)

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from groups.schemas import DetailResponse, GroupCreateSchema, GroupDetailRead, GroupMemberCreateSchema, GroupMemberRead, GroupMessageRead, GroupMessageUpdateSchema, GroupReactionCreateSchema, GroupRead, GroupUpdateSchema, MembersCountRead
from groups.views import add_group_member, add_group_message_reaction, create_group, delete_group, delete_group_message, edit_group_message, get_group_detail, get_group_members, get_group_members_count, get_group_messages, get_groups, make_group_admin, pin_group_message, remove_group_member, search_groups, send_group_message, unpin_group_message, update_group
from users.auth import get_current_user
from users.models import User


groups_router = APIRouter(prefix="/groups", tags=["Groups"])


@groups_router.get("/", response_model=list[GroupRead])
def groups_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_groups(db, current_user)


@groups_router.post("/", response_model=GroupDetailRead, status_code=201)
def create_new_group(
    name: str = Form(...),
    description: str | None = Form(None),
    avatar: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = GroupCreateSchema(
        name=name,
        description=description,
    )

    return create_group(data, avatar, db, current_user)


@groups_router.get("/search", response_model=list[GroupRead])
def groups_search(q: str = Query(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return search_groups(q, db, current_user)


@groups_router.get("/{group_id}", response_model=GroupDetailRead)
def group_detail(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_group_detail(group_id, db, current_user)


@groups_router.delete("/{group_id}", response_model=DetailResponse)
def remove_group(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return delete_group(group_id, db, current_user)


@groups_router.put("/{group_id}", response_model=GroupDetailRead)
def update_group_info(
    group_id: int,
    name: str | None = Form(None),
    description: str | None = Form(None),
    avatar: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = GroupUpdateSchema(
        name=name,
        description=description,
    )

    return update_group(group_id, data, avatar, db, current_user)


@groups_router.get("/{group_id}/members/count", response_model=MembersCountRead)
def group_members_count(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_group_members_count(group_id, db, current_user)


@groups_router.get("/{group_id}/members", response_model=list[GroupMemberRead])
def group_members(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_group_members(group_id, db, current_user)


@groups_router.post("/{group_id}/members", response_model=GroupMemberRead, status_code=201)
def create_group_member(
    group_id: int,
    data: GroupMemberCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return add_group_member(group_id, data, db, current_user)


@groups_router.delete("/{group_id}/members/{username}", response_model=DetailResponse)
def delete_group_member(group_id: int, username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return remove_group_member(group_id, username, db, current_user)


@groups_router.post("/{group_id}/members/{username}/admin", response_model=GroupMemberRead)
def add_group_admin(group_id: int, username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return make_group_admin(group_id, username, db, current_user)


@groups_router.get("/{group_id}/messages", response_model=list[GroupMessageRead])
def group_messages(
    group_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_group_messages(group_id, db, current_user, limit, offset)


@groups_router.post("/{group_id}/messages", response_model=GroupMessageRead, status_code=201)
def create_group_message(
    group_id: int,
    text: str | None = Form(None),
    reply_to_id: int | None = Form(None),
    forwarded_from_id: int | None = Form(None),
    media: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return send_group_message(group_id, text, reply_to_id, forwarded_from_id, media, db, current_user)


@groups_router.put("/{group_id}/messages/{message_id}", response_model=GroupMessageRead)
def update_group_message(
    group_id: int,
    message_id: int,
    data: GroupMessageUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return edit_group_message(group_id, message_id, data, db, current_user)


@groups_router.delete("/{group_id}/messages/{message_id}", response_model=DetailResponse)
def remove_group_message(group_id: int, message_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return delete_group_message(group_id, message_id, db, current_user)


@groups_router.post("/{group_id}/messages/{message_id}/pin", response_model=GroupMessageRead)
def pin_message_in_group(group_id: int, message_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return pin_group_message(group_id, message_id, db, current_user)


@groups_router.post("/{group_id}/messages/{message_id}/unpin", response_model=DetailResponse)
def unpin_message_in_group(group_id: int, message_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return unpin_group_message(group_id, message_id, db, current_user)


@groups_router.post("/{group_id}/messages/{message_id}/reactions", response_model=GroupMessageRead)
def create_group_message_reaction(
    group_id: int,
    message_id: int,
    data: GroupReactionCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return add_group_message_reaction(group_id, message_id, data, db, current_user)

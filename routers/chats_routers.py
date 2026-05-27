from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from chats.schemas import ChatCreateSchema, ChatRead, DetailResponse, MessageRead, MessageUpdateSchema, ReactionCreateSchema, UnifiedChatRead
from chats.views import add_message_reaction, create_or_get_chat, delete_message, edit_message, get_chat_messages, get_chats, get_unified_chats, pin_message, send_message
from database import get_db
from users.auth import get_current_user
from users.models import User


chats_router = APIRouter(prefix="/chats", tags=["Chats"])


@chats_router.get("/", response_model=list[ChatRead])
def chats_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_chats(db, current_user)


@chats_router.post("/", response_model=ChatRead, status_code=201)
def create_chat(data: ChatCreateSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return create_or_get_chat(data, db, current_user)


@chats_router.get("/all", response_model=list[UnifiedChatRead])
def all_chats_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_unified_chats(db, current_user)


@chats_router.get("/{chat_id}/messages", response_model=list[MessageRead])
def chat_messages(chat_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_chat_messages(chat_id, db, current_user)


@chats_router.post("/{chat_id}/messages", response_model=MessageRead, status_code=201)
def create_message(
    chat_id: int,
    text: str | None = Form(None),
    reply_to_id: int | None = Form(None),
    forwarded_from_id: int | None = Form(None),
    media: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return send_message(chat_id, text, reply_to_id, forwarded_from_id, media, db, current_user)


@chats_router.put("/{chat_id}/messages/{message_id}", response_model=MessageRead)
def update_message(
    chat_id: int,
    message_id: int,
    data: MessageUpdateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return edit_message(chat_id, message_id, data, db, current_user)


@chats_router.delete("/{chat_id}/messages/{message_id}", response_model=DetailResponse)
def remove_message(chat_id: int, message_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return delete_message(chat_id, message_id, db, current_user)


@chats_router.post("/{chat_id}/messages/{message_id}/pin", response_model=MessageRead)
def pin_chat_message(chat_id: int, message_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return pin_message(chat_id, message_id, db, current_user)


@chats_router.post("/{chat_id}/messages/{message_id}/reactions", response_model=MessageRead)
def create_message_reaction(
    chat_id: int,
    message_id: int,
    data: ReactionCreateSchema,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return add_message_reaction(chat_id, message_id, data, db, current_user)

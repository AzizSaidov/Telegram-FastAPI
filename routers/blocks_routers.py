from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from blocks.schemas import BlockedUserRead, BlockUserSchema, DetailResponse
from blocks.views import block_user, get_blocked_users, unblock_user
from database import get_db
from users.auth import get_current_user
from users.models import User


blocks_router = APIRouter(prefix="/blocks", tags=["Blocks"])


@blocks_router.get("/", response_model=list[BlockedUserRead])
def blocked_users_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_blocked_users(db, current_user)


@blocks_router.post("/", response_model=BlockedUserRead, status_code=201)
def create_blocked_user(data: BlockUserSchema, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return block_user(data, db, current_user)


@blocks_router.delete("/{username}", response_model=DetailResponse)
def remove_blocked_user(username: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return unblock_user(username, db, current_user)

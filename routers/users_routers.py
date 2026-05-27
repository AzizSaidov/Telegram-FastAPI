from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from users.auth import get_current_user
from users.models import User
from users.schemas import AuthResponse, LogoutResponse, UserLoginSchema, UserRegisterSchema
from users.views import login_user, logout_user, register_user


users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.post("/register", response_model=AuthResponse, status_code=201)
def register(data: UserRegisterSchema, db: Session = Depends(get_db)):
    return register_user(data, db)


@users_router.post("/login", response_model=AuthResponse)
def login(data: UserLoginSchema, db: Session = Depends(get_db)):
    return login_user(data, db)


@users_router.post("/logout", response_model=LogoutResponse)
def logout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return logout_user(db, current_user.id)

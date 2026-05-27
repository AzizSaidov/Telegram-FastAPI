from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from users.auth import get_current_user
from users.models import User
from users.schemas import AuthResponse, LogoutResponse, OTPResponse, PhoneNumberSchema, UserSearchRead, VerifyOTPSchema
from users.views import logout_user, request_otp, search_users, verify_otp


users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.post("/request-otp", response_model=OTPResponse)
def create_otp(data: PhoneNumberSchema, db: Session = Depends(get_db)):
    return request_otp(data, db)


@users_router.post("/verify-otp", response_model=AuthResponse)
def verify_login_otp(data: VerifyOTPSchema, db: Session = Depends(get_db)):
    return verify_otp(data, db)


@users_router.post("/logout", response_model=LogoutResponse)
def logout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return logout_user(db, current_user.id)


@users_router.get("/search", response_model=list[UserSearchRead])
def users_search(q: str = Query(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return search_users(q, db, current_user)

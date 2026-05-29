from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from users.auth import get_current_user
from users.models import User
from users.schemas import (
    AuthResponse,
    LogoutResponse,
    OTPResponse,
    PhoneNumberSchema,
    RegisterRequestSchema,
    RegisterVerifyOTPSchema,
    UserSearchRead,
    VerifyOTPSchema,
)
from users.views import (
    logout_user,
    request_login_otp,
    request_register_otp,
    search_user_by_phone,
    search_users,
    verify_login_otp,
    verify_register_otp,
)


users_router = APIRouter(prefix="/users", tags=["Users"])


@users_router.post("/login/request-otp", response_model=OTPResponse)
def create_login_otp(data: PhoneNumberSchema, db: Session = Depends(get_db)):
    return request_login_otp(data, db)


@users_router.post("/login/verify-otp", response_model=AuthResponse)
def verify_login_code(data: VerifyOTPSchema, db: Session = Depends(get_db)):
    return verify_login_otp(data, db)


@users_router.post("/register/request-otp", response_model=OTPResponse)
def create_register_otp(data: RegisterRequestSchema, db: Session = Depends(get_db)):
    return request_register_otp(data, db)


@users_router.post("/register/verify-otp", response_model=AuthResponse)
def verify_register_code(data: RegisterVerifyOTPSchema, db: Session = Depends(get_db)):
    return verify_register_otp(data, db)


@users_router.post("/logout", response_model=LogoutResponse)
def logout(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return logout_user(db, current_user.id)


@users_router.get("/search/phone", response_model=UserSearchRead)
def users_search_phone(
    phone_number: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return search_user_by_phone(phone_number, db, current_user)


@users_router.get("/search", response_model=list[UserSearchRead])
def users_search(q: str = Query(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return search_users(q, db, current_user)

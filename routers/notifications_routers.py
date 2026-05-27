from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from notifications.schemas import DetailResponse, NotificationRead
from notifications.views import get_notifications, mark_all_notifications_as_read, mark_notification_as_read
from users.auth import get_current_user
from users.models import User


notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@notifications_router.get("/", response_model=list[NotificationRead])
def notifications_list(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_notifications(db, current_user)


@notifications_router.post("/read-all", response_model=DetailResponse)
def read_all_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return mark_all_notifications_as_read(db, current_user)


@notifications_router.post("/{notification_id}/read", response_model=NotificationRead)
def read_notification(notification_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return mark_notification_as_read(notification_id, db, current_user)

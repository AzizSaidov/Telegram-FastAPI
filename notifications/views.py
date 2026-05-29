from fastapi import HTTPException
from sqlalchemy.orm import Session

from notifications.models import Notification
from sockets.schemas import EVENT_NOTIFICATION_CREATED, socket_event
from sockets.utils import send_socket_event_to_user
from users.models import User


NOTIFICATION_TYPES = [
    "message",
    "group_message",
    "channel_post",
    "reaction",
    "mention",
]


def build_notification_event_data(notification: Notification):
    from_user = notification.from_user
    profile = from_user.profile if from_user else None

    return {
        "id": notification.id,
        "type": notification.type,
        "entity_id": notification.entity_id,
        "entity_type": notification.entity_type,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat(),
        "from_user": {
            "id": from_user.id,
            "profile": {
                "username": profile.username if profile else None,
                "full_name": profile.full_name if profile else None,
                "avatar_url": profile.avatar_url if profile else None,
                "is_online": profile.is_online if profile else False,
                "last_seen": profile.last_seen.isoformat() if profile and profile.last_seen else None,
            },
        } if from_user else None,
    }


def create_notification(
    db: Session,
    to_user_id: int,
    from_user_id: int,
    notification_type: str,
    entity_id: int,
    entity_type: str,
):
    if to_user_id == from_user_id:
        return None

    if notification_type not in NOTIFICATION_TYPES:
        raise HTTPException(status_code=400, detail="Invalid notification type")

    new_notification = Notification(
        to_user_id=to_user_id,
        from_user_id=from_user_id,
        type=notification_type,
        entity_id=entity_id,
        entity_type=entity_type,
    )

    db.add(new_notification)
    db.commit()
    db.refresh(new_notification)

    send_socket_event_to_user(
        to_user_id,
        socket_event(EVENT_NOTIFICATION_CREATED, build_notification_event_data(new_notification)),
    )

    return new_notification


def get_notifications(db: Session, current_user: User, limit: int, offset: int):
    return db.query(Notification).filter(
        Notification.to_user_id == current_user.id,
    ).order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()


def mark_notification_as_read(notification_id: int, db: Session, current_user: User):
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.to_user_id == current_user.id,
    ).first()

    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification


def mark_all_notifications_as_read(db: Session, current_user: User):
    db.query(Notification).filter(
        Notification.to_user_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()

    return {"detail": "Notifications marked as read"}

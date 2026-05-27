from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from database import get_db
from profiles.models import Profile
from sockets.manager import manager
from sockets.schemas import EVENT_CONNECTION_ESTABLISHED, EVENT_ERROR, EVENT_TYPING_STARTED, EVENT_TYPING_STOPPED, EVENT_USER_OFFLINE, EVENT_USER_ONLINE, socket_event
from users.auth import get_user_from_token
from users.models import User
from utils import get_dushanbe_time


sockets_router = APIRouter(tags=["WebSocket"])


def get_user_for_socket(token: str | None, db: Session):
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is required")

    return get_user_from_token(token, db, "access")


def set_profile_online(user: User, db: Session):
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()

    if profile is None:
        return None

    profile.is_online = True
    db.commit()
    db.refresh(profile)

    return profile


def set_profile_offline(user: User, db: Session):
    profile = db.query(Profile).filter(Profile.user_id == user.id).first()

    if profile is None:
        return None

    profile.is_online = False
    profile.last_seen = get_dushanbe_time()
    db.commit()
    db.refresh(profile)

    return profile


def profile_status_data(user: User, profile: Profile | None):
    return {
        "user_id": user.id,
        "username": profile.username if profile else None,
        "is_online": profile.is_online if profile else False,
        "last_seen": profile.last_seen.isoformat() if profile and profile.last_seen else None,
    }


async def handle_typing_event(current_user: User, data: dict, event_type: str):
    user_ids = data.get("to_user_ids", [])

    if not isinstance(user_ids, list):
        return

    payload = data.copy()
    payload["from_user_id"] = current_user.id

    await manager.broadcast_to_users(user_ids, socket_event(event_type, payload))


@sockets_router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None),
    db: Session = Depends(get_db),
):
    try:
        current_user = get_user_for_socket(token, db)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    was_connected = manager.is_user_connected(current_user.id)
    await manager.connect(current_user.id, websocket)
    profile = set_profile_online(current_user, db)

    if not was_connected:
        await manager.broadcast(socket_event(EVENT_USER_ONLINE, profile_status_data(current_user, profile)))

    await manager.send_to_user(
        current_user.id,
        socket_event(EVENT_CONNECTION_ESTABLISHED, profile_status_data(current_user, profile)),
    )

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            event_data = data.get("data", {})

            if not isinstance(event_data, dict):
                await manager.send_to_user(current_user.id, socket_event(EVENT_ERROR, {"detail": "Invalid event data"}))
                continue

            if event_type in [EVENT_TYPING_STARTED, EVENT_TYPING_STOPPED]:
                await handle_typing_event(current_user, event_data, event_type)
            else:
                await manager.send_to_user(current_user.id, socket_event(EVENT_ERROR, {"detail": "Unknown event type"}))

    except WebSocketDisconnect:
        manager.disconnect(current_user.id, websocket)

        if not manager.is_user_connected(current_user.id):
            profile = set_profile_offline(current_user, db)
            await manager.broadcast(socket_event(EVENT_USER_OFFLINE, profile_status_data(current_user, profile)))

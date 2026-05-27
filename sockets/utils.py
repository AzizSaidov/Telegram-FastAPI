from anyio import from_thread

from sockets.manager import manager


def send_socket_event_to_user(user_id: int, data: dict):
    try:
        from_thread.run(manager.send_to_user, user_id, data)
    except RuntimeError:
        return None


def broadcast_socket_event_to_users(user_ids: list[int], data: dict):
    try:
        from_thread.run(manager.broadcast_to_users, user_ids, data)
    except RuntimeError:
        return None

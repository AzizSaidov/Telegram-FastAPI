EVENT_CONNECTION_ESTABLISHED = "connection_established"
EVENT_ERROR = "error"

EVENT_TYPING_STARTED = "typing_started"
EVENT_TYPING_STOPPED = "typing_stopped"
EVENT_USER_ONLINE = "user_online"
EVENT_USER_OFFLINE = "user_offline"

EVENT_MESSAGE_CREATED = "message_created"
EVENT_MESSAGE_UPDATED = "message_updated"
EVENT_MESSAGE_DELETED = "message_deleted"
EVENT_REACTION_CREATED = "reaction_created"
EVENT_GROUP_MESSAGE_CREATED = "group_message_created"
EVENT_CHANNEL_POST_CREATED = "channel_post_created"
EVENT_NOTIFICATION_CREATED = "notification_created"


def socket_event(event_type: str, data: dict | None = None):
    return {
        "type": event_type,
        "data": data or {},
    }

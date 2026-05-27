from datetime import timedelta
from html import escape
from pathlib import Path

from blocks.models import BlockedUser
from channels.models import Channel, ChannelMember, ChannelPost, ChannelPostReaction, ChannelReadState
from chats.models import Chat, Message, MessageReaction
from contacts.models import Contact
from database import Base, SessionLocal, engine
from groups.models import Group, GroupMember, GroupMessage, GroupMessageReaction, GroupReadState
from notifications.models import Notification
from polls.models import Poll, PollOption, PollVote
from profiles.models import Profile
from stories.models import Story, StoryView
from users.models import User
from utils import get_dushanbe_time


MEDIA_ROOT = Path("media") / "seed"


def media_url(path: Path):
    return f"/{path.as_posix()}"


def write_svg(path: Path, title: str, color: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    initials = "".join(part[:1] for part in title.split()[:2]).upper() or "TG"
    safe_title = escape(title)
    safe_initials = escape(initials)

    path.write_text(
        f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800" viewBox="0 0 800 800">
<rect width="800" height="800" fill="{color}"/>
<circle cx="400" cy="315" r="132" fill="#ffffff" fill-opacity="0.22"/>
<rect x="176" y="500" width="448" height="96" rx="48" fill="#ffffff" fill-opacity="0.18"/>
<text x="400" y="360" text-anchor="middle" font-size="112" font-family="Arial" font-weight="700" fill="#ffffff">{safe_initials}</text>
<text x="400" y="680" text-anchor="middle" font-size="42" font-family="Arial" font-weight="700" fill="#ffffff">{safe_title}</text>
</svg>
""",
        encoding="utf-8",
    )


def create_seed_media():
    media_items = {
        "avatars/aziz.svg": ("Aziz Saidov", "#2AABEE"),
        "avatars/malika.svg": ("Malika Karimova", "#8B5CF6"),
        "avatars/farhod.svg": ("Farhod Rahmon", "#10B981"),
        "avatars/zebo.svg": ("Zebo Nazarova", "#F97316"),
        "avatars/davron.svg": ("Davron Olimov", "#EF4444"),
        "avatars/sabrina.svg": ("Sabrina Yusuf", "#EC4899"),
        "avatars/rustam.svg": ("Rustam Latifi", "#14B8A6"),
        "avatars/nozim.svg": ("Nozim Test", "#64748B"),
        "avatars/group_team.svg": ("Clone Team", "#334155"),
        "avatars/channel_tech.svg": ("Tech Pulse", "#2563EB"),
        "avatars/channel_movies.svg": ("Movie Club", "#7C3AED"),
        "avatars/channel_private.svg": ("Private Notes", "#0F766E"),
    }

    for index in range(1, 13):
        media_items[f"stories/story_{index}.svg"] = (f"Story {index}", "#2AABEE" if index % 2 else "#8B5CF6")

    for index in range(1, 7):
        media_items[f"chats/photo_{index}.svg"] = (f"Chat Photo {index}", "#1D4ED8")
        media_items[f"groups/photo_{index}.svg"] = (f"Group Photo {index}", "#059669")
        media_items[f"channels/photo_{index}.svg"] = (f"Channel Photo {index}", "#DC2626")

    for relative_path, (title, color) in media_items.items():
        write_svg(MEDIA_ROOT / relative_path, title, color)


def create_user(db, phone_number: str, username: str, full_name: str, bio: str, avatar: str, is_online: bool):
    now = get_dushanbe_time()
    user = User(
        phone_number=phone_number,
        created_at=now - timedelta(days=12),
    )
    db.add(user)
    db.flush()

    profile = Profile(
        user_id=user.id,
        username=username,
        full_name=full_name,
        bio=bio,
        avatar_url=avatar,
        is_online=is_online,
        last_seen=None if is_online else now - timedelta(minutes=20 + user.id * 7),
        created_at=now - timedelta(days=12),
    )
    db.add(profile)
    db.flush()

    user.profile = profile

    return user


def create_users(db):
    users_data = [
        ("+992900000001", "aziz", "Aziz Saidov", "Backend owner. Building Telegram clone.", "aziz.svg", True),
        ("+992900000002", "malika", "Malika Karimova", "Frontend and UI polish.", "malika.svg", True),
        ("+992900000003", "farhod", "Farhod Rahmon", "FastAPI, SQLAlchemy, WebSocket.", "farhod.svg", False),
        ("+992900000004", "zebo", "Zebo Nazarova", "QA and product notes.", "zebo.svg", False),
        ("+992900000005", "davron", "Davron Olimov", "Mobile testing and release checks.", "davron.svg", True),
        ("+992900000006", "sabrina", "Sabrina Yusuf", "Content and channel posts.", "sabrina.svg", False),
        ("+992900000007", "rustam", "Rustam Latifi", "Design system experiments.", "rustam.svg", False),
        ("+992900000008", "nozim", "Nozim Test", "Blocked test account.", "nozim.svg", False),
    ]

    users = {}

    for phone, username, full_name, bio, avatar, is_online in users_data:
        users[username] = create_user(
            db,
            phone,
            username,
            full_name,
            bio,
            media_url(MEDIA_ROOT / "avatars" / avatar),
            is_online,
        )

    return users


def create_contacts_and_blocks(db, users):
    contacts = [
        ("aziz", "malika", "Malika"),
        ("aziz", "farhod", "Farhod"),
        ("aziz", "zebo", "Zebo QA"),
        ("aziz", "davron", "Davron"),
        ("aziz", "sabrina", "Sabrina"),
        ("malika", "aziz", "Aziz"),
        ("malika", "farhod", "Farhod API"),
        ("farhod", "aziz", "Aziz Backend"),
        ("zebo", "malika", "Malika UI"),
        ("davron", "aziz", "Aziz"),
    ]

    for owner, contact, name in contacts:
        db.add(Contact(
            owner_id=users[owner].id,
            contact_id=users[contact].id,
            name=name,
        ))

    db.add(BlockedUser(
        blocker_id=users["aziz"].id,
        blocked_id=users["nozim"].id,
    ))
    db.add(BlockedUser(
        blocker_id=users["zebo"].id,
        blocked_id=users["rustam"].id,
    ))


def create_private_chat(db, users):
    now = get_dushanbe_time()
    aziz = users["aziz"]
    malika = users["malika"]
    chat = Chat(
        user_id_1=min(aziz.id, malika.id),
        user_id_2=max(aziz.id, malika.id),
        created_at=now - timedelta(days=5),
    )
    db.add(chat)
    db.flush()

    texts = [
        "Hey, I checked auth and profile responses.",
        "Nice, I will test the React layout with real data.",
        "Messages now have reply and forward examples.",
        "Good. I need avatars and stories too.",
        "Seed script will generate local media placeholders.",
        "Perfect, then Sidebar will not look empty.",
        "Pinned message should appear at the top.",
        "This one is pinned for the private chat.",
        "Can we upload photo or video later?",
        "Yes, backend stores files under media folders.",
        "Unread count must work for incoming messages.",
        "I left a few messages unread for Aziz.",
        "Forwarded message example is coming next.",
        "This message points to an older forwarded item.",
        "Search should find users by username.",
        "And channels by name or description.",
        "The poll is only inside a channel post.",
        "Right, groups have no polls now.",
        "Pagination returns newest messages first.",
        "Frontend can reverse them for display.",
        "Let's keep API responses simple.",
        "No top-level message wrappers everywhere.",
        "Only detail for delete and read actions.",
        "I like this shape.",
        "We should test WebSocket next.",
        "Yes, after seed data is ready.",
        "Last messages help the chat list.",
        "This one should appear near the top.",
        "Final unread message from Malika.",
        "One more unread message for badge testing.",
    ]

    messages = []

    for index, text in enumerate(texts, start=1):
        sender = aziz if index % 2 else malika
        media = media_url(MEDIA_ROOT / "chats" / f"photo_{((index - 1) % 6) + 1}.svg") if index in [5, 11, 18, 26] else None
        message = Message(
            chat_id=chat.id,
            sender_id=sender.id,
            text=text,
            media_url=media,
            reply_to_id=messages[-1].id if index in [4, 8, 17, 24] else None,
            forwarded_from_id=messages[2].id if index == 14 else None,
            is_edited=index in [9, 22],
            is_read=False if sender.id == malika.id and index >= 27 else True,
            is_pinned=index == 8,
            created_at=now - timedelta(minutes=90 - index * 2),
        )
        db.add(message)
        db.flush()
        messages.append(message)

    reactions = [
        (messages[2], malika, "👍"),
        (messages[4], aziz, "🔥"),
        (messages[7], malika, "📌"),
        (messages[13], aziz, "👌"),
        (messages[21], malika, "💙"),
        (messages[27], aziz, "👀"),
    ]

    for message, user, emoji in reactions:
        db.add(MessageReaction(
            message_id=message.id,
            user_id=user.id,
            emoji=emoji,
            created_at=message.created_at + timedelta(minutes=1),
        ))

    return chat, messages


def create_group(db, users):
    now = get_dushanbe_time()
    group = Group(
        owner_id=users["aziz"].id,
        name="Telegram Clone Team",
        avatar_url=media_url(MEDIA_ROOT / "avatars" / "group_team.svg"),
        description="Development group for FastAPI and React Telegram clone.",
        created_at=now - timedelta(days=4),
    )
    db.add(group)
    db.flush()

    members = [
        ("aziz", "admin"),
        ("malika", "admin"),
        ("farhod", "member"),
        ("zebo", "member"),
        ("davron", "member"),
        ("sabrina", "member"),
    ]

    for username, role in members:
        db.add(GroupMember(
            group_id=group.id,
            user_id=users[username].id,
            role=role,
            joined_at=now - timedelta(days=4),
        ))

    db.flush()

    senders = ["aziz", "malika", "farhod", "zebo", "davron", "sabrina"]
    messages = []

    for index in range(1, 36):
        sender = users[senders[index % len(senders)]]
        media = media_url(MEDIA_ROOT / "groups" / f"photo_{((index - 1) % 6) + 1}.svg") if index in [6, 13, 21, 30] else None
        message = GroupMessage(
            group_id=group.id,
            sender_id=sender.id,
            text=f"Group update #{index}: testing members, replies, pins, reactions and unread state.",
            media_url=media,
            reply_to_id=messages[-1].id if index in [7, 14, 22, 31] else None,
            forwarded_from_id=messages[4].id if index == 18 else None,
            is_edited=index in [12, 28],
            is_pinned=index == 10,
            created_at=now - timedelta(minutes=120 - index * 2),
        )
        db.add(message)
        db.flush()
        messages.append(message)

    for index, message in enumerate(messages[4::5], start=1):
        user = users[senders[index % len(senders)]]
        db.add(GroupMessageReaction(
            message_id=message.id,
            user_id=user.id,
            emoji=["👍", "🔥", "👏", "💙"][index % 4],
            created_at=message.created_at + timedelta(minutes=2),
        ))

    db.add(GroupReadState(
        group_id=group.id,
        user_id=users["aziz"].id,
        last_read_message_id=messages[-8].id,
        updated_at=now - timedelta(minutes=10),
    ))

    return group, messages


def create_channel_with_posts(db, users, owner: str, name: str, avatar: str, description: str, is_public: bool, members: list[tuple[str, str]], posts_count: int):
    now = get_dushanbe_time()
    channel = Channel(
        owner_id=users[owner].id,
        name=name,
        avatar_url=media_url(MEDIA_ROOT / "avatars" / avatar),
        description=description,
        is_public=is_public,
        created_at=now - timedelta(days=3),
    )
    db.add(channel)
    db.flush()

    for username, role in members:
        db.add(ChannelMember(
            channel_id=channel.id,
            user_id=users[username].id,
            role=role,
            joined_at=now - timedelta(days=3),
        ))

    db.flush()

    admin_usernames = [username for username, role in members if role == "admin"]
    posts = []

    for index in range(1, posts_count + 1):
        sender = users[admin_usernames[index % len(admin_usernames)]]
        media = media_url(MEDIA_ROOT / "channels" / f"photo_{((index - 1) % 6) + 1}.svg") if index in [2, 5, 8, 11] else None
        post = ChannelPost(
            channel_id=channel.id,
            sender_id=sender.id,
            text=f"{name} post #{index}: news, media, reactions and channel feed testing.",
            media_url=media,
            is_edited=index in [4, 9],
            is_pinned=index == 3,
            created_at=now - timedelta(minutes=posts_count * 4 - index * 4),
        )
        db.add(post)
        db.flush()
        posts.append(post)

    subscriber_usernames = [username for username, role in members if role == "subscriber"]

    for index, post in enumerate(posts):
        for username in subscriber_usernames[:3]:
            if (index + users[username].id) % 2 == 0:
                db.add(ChannelPostReaction(
                    post_id=post.id,
                    user_id=users[username].id,
                    emoji=["👍", "🔥", "💙", "👀"][index % 4],
                    created_at=post.created_at + timedelta(minutes=1),
                ))

    if any(username == "aziz" for username, _ in members) and len(posts) > 4:
        db.add(ChannelReadState(
            channel_id=channel.id,
            user_id=users["aziz"].id,
            last_read_post_id=posts[-4].id,
            updated_at=now - timedelta(minutes=7),
        ))

    return channel, posts


def create_channels(db, users):
    tech, tech_posts = create_channel_with_posts(
        db,
        users,
        owner="farhod",
        name="Tech Pulse",
        avatar="channel_tech.svg",
        description="Public channel with FastAPI, React and WebSocket updates.",
        is_public=True,
        members=[
            ("farhod", "admin"),
            ("aziz", "subscriber"),
            ("malika", "subscriber"),
            ("zebo", "subscriber"),
            ("davron", "subscriber"),
            ("rustam", "subscriber"),
        ],
        posts_count=12,
    )
    movies, movie_posts = create_channel_with_posts(
        db,
        users,
        owner="sabrina",
        name="Movie Club",
        avatar="channel_movies.svg",
        description="Public channel for film picks and weekend watchlists.",
        is_public=True,
        members=[
            ("sabrina", "admin"),
            ("malika", "subscriber"),
            ("rustam", "subscriber"),
            ("zebo", "subscriber"),
        ],
        posts_count=8,
    )
    private, private_posts = create_channel_with_posts(
        db,
        users,
        owner="aziz",
        name="Private Backend Notes",
        avatar="channel_private.svg",
        description="Private channel visible only to invited members.",
        is_public=False,
        members=[
            ("aziz", "admin"),
            ("malika", "subscriber"),
            ("davron", "subscriber"),
        ],
        posts_count=6,
    )

    poll = Poll(
        channel_post_id=tech_posts[2].id,
        question="Which feature should we test first?",
        created_at=tech_posts[2].created_at + timedelta(minutes=1),
    )
    db.add(poll)
    db.flush()

    options = []

    for text in ["Auth flow", "WebSocket realtime", "Media upload", "Notifications"]:
        option = PollOption(
            poll_id=poll.id,
            text=text,
        )
        db.add(option)
        db.flush()
        options.append(option)

    votes = [
        ("aziz", options[1]),
        ("malika", options[2]),
        ("zebo", options[1]),
        ("davron", options[3]),
        ("rustam", options[0]),
    ]

    for username, option in votes:
        db.add(PollVote(
            poll_id=poll.id,
            option_id=option.id,
            user_id=users[username].id,
            created_at=poll.created_at + timedelta(minutes=3),
        ))

    return {
        "tech": (tech, tech_posts),
        "movies": (movies, movie_posts),
        "private": (private, private_posts),
    }


def create_stories(db, users):
    now = get_dushanbe_time()
    story_owners = ["aziz", "malika", "farhod", "zebo", "davron", "sabrina"]
    stories = []
    story_index = 1

    for owner in story_owners:
        for _ in range(2):
            story = Story(
                user_id=users[owner].id,
                media_url=media_url(MEDIA_ROOT / "stories" / f"story_{story_index}.svg"),
                media_type="photo",
                expires_at=now + timedelta(hours=24 - story_index),
                created_at=now - timedelta(hours=story_index),
            )
            db.add(story)
            db.flush()
            stories.append(story)
            story_index += 1

    for story in stories:
        for username in ["aziz", "malika", "farhod", "zebo"]:
            if users[username].id != story.user_id and (story.id + users[username].id) % 2 == 0:
                db.add(StoryView(
                    story_id=story.id,
                    user_id=users[username].id,
                    created_at=story.created_at + timedelta(minutes=10),
                ))

    return stories


def create_notifications(db, users, chat_messages, group_messages, channels):
    now = get_dushanbe_time()
    tech_posts = channels["tech"][1]
    private_posts = channels["private"][1]
    notifications = [
        (users["aziz"], users["malika"], "message", chat_messages[-1].id, "message", False),
        (users["aziz"], users["farhod"], "group_message", group_messages[-1].id, "group_message", False),
        (users["aziz"], users["farhod"], "channel_post", tech_posts[-1].id, "channel_post", False),
        (users["aziz"], users["malika"], "reaction", chat_messages[7].id, "message", True),
        (users["malika"], users["aziz"], "channel_post", private_posts[-1].id, "channel_post", False),
        (users["farhod"], users["zebo"], "mention", group_messages[11].id, "group_message", True),
    ]

    for index, (to_user, from_user, notification_type, entity_id, entity_type, is_read) in enumerate(notifications, start=1):
        db.add(Notification(
            to_user_id=to_user.id,
            from_user_id=from_user.id,
            type=notification_type,
            entity_id=entity_id,
            entity_type=entity_type,
            is_read=is_read,
            created_at=now - timedelta(minutes=30 - index * 3),
        ))


def seed_database():
    create_seed_media()

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        users = create_users(db)
        create_contacts_and_blocks(db, users)
        _, chat_messages = create_private_chat(db, users)
        _, group_messages = create_group(db, users)
        channels = create_channels(db, users)
        create_stories(db, users)
        create_notifications(db, users, chat_messages, group_messages, channels)

        db.commit()
    finally:
        db.close()

    print("Seed data created successfully.")
    print("Main phone number: +992900000001")
    print("Use POST /users/request-otp, then POST /users/verify-otp with the OTP code from Swagger.")
    print("Users: aziz, malika, farhod, zebo, davron, sabrina, rustam, nozim")
    print("Channels: Tech Pulse public, Movie Club public, Private Backend Notes private")


if __name__ == "__main__":
    seed_database()

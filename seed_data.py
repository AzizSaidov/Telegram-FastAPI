from __future__ import annotations

import math
import shutil
import urllib.request
from datetime import timedelta
from io import BytesIO
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

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
from users.models import OTPCode, User
from utils import get_dushanbe_time


MEDIA_ROOT = Path("media") / "seed"
FONT_REGULAR = Path("C:/Windows/Fonts/arial.ttf")
FONT_BOLD = Path("C:/Windows/Fonts/arialbd.ttf")
CURRENT_USER = "aziz"


# ── helpers ──────────────────────────────────────────────────────────────────

def media_url(path: Path) -> str:
    return f"/{path.as_posix()}"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold and FONT_BOLD.exists() else FONT_REGULAR
    if path.exists():
        return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def lerp(a: int, b: int, t: float) -> int:
    return int(a + (b - a) * t)


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def gradient(size: tuple[int, int], colors: tuple[str, str], vertical: bool = True) -> Image.Image:
    w, h = size
    c1, c2 = hex_to_rgb(colors[0]), hex_to_rgb(colors[1])
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = y / max(1, h - 1) if vertical else x / max(1, w - 1)
            px[x, y] = tuple(lerp(c1[i], c2[i], t) for i in range(3))
    return img


def draw_center_text(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt, fill: str) -> None:
    bbox = draw.textbbox((0, 0), text, font=fnt)
    draw.text((xy[0] - (bbox[2] - bbox[0]) / 2, xy[1] - (bbox[3] - bbox[1]) / 2), text, font=fnt, fill=fill)


def fetch_picsum(seed: str, width: int, height: int) -> Image.Image | None:
    """Download a real photo from picsum.photos. Returns None on failure."""
    try:
        url = f"https://picsum.photos/seed/{seed}/{width}/{height}"
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = resp.read()
        return Image.open(BytesIO(data)).convert("RGBA").resize((width, height), Image.LANCZOS)
    except Exception:
        return None


# ── avatar: Telegram-style gradient + large initials ─────────────────────────

def save_avatar(path: Path, name: str, colors: tuple[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    size = 640
    img = gradient((size, size), colors).convert("RGBA")

    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((-80, -80, 420, 420), fill=(255, 255, 255, 20))
    glow = glow.filter(ImageFilter.GaussianBlur(70))
    img = Image.alpha_composite(img, glow)

    initials = "".join(p[0] for p in name.split()[:2]).upper()
    draw_center_text(ImageDraw.Draw(img), (size // 2, size // 2), initials, font(210, bold=True), "#ffffff")

    img.convert("RGB").save(path, quality=92)


# ── landscape photo: real picsum + dark bottom overlay + text ────────────────

def save_photo(path: Path, picsum_seed: str, title: str, subtitle: str, fallback_colors: tuple[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    w, h = 1280, 720

    img = fetch_picsum(picsum_seed, w, h)
    if img is None:
        img = gradient((w, h), fallback_colors, vertical=False).convert("RGBA")

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ov = ImageDraw.Draw(overlay)
    for y in range(h // 2, h):
        a = int(195 * (y - h // 2) / (h // 2))
        ov.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)
    draw.text((52, h - 128), title, font=font(46, True), fill="#ffffff")
    draw.text((54, h - 70), subtitle, font=font(27), fill="#dbeafe")

    img.convert("RGB").save(path, quality=92)


# ── portrait photo: real picsum + bottom overlay + text ──────────────────────

def save_story_photo(path: Path, picsum_seed: str, title: str, subtitle: str, fallback_colors: tuple[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    w, h = 720, 1280

    img = fetch_picsum(picsum_seed, w, h)
    if img is None:
        img = gradient((w, h), fallback_colors).convert("RGBA")

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ov = ImageDraw.Draw(overlay)
    start = h * 2 // 3
    for y in range(start, h):
        a = int(215 * (y - start) / (h - start))
        ov.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)
    draw.text((44, h - 188), title, font=font(42, True), fill="#ffffff")
    draw.text((46, h - 130), subtitle, font=font(27), fill="#e0f2fe")

    img.convert("RGB").save(path, quality=92)


# ── story video: animated gradient (videos can't be downloaded easily) ───────

def save_story_video(path: Path, title: str, colors: tuple[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = []
    w, h = 384, 640
    for fi in range(48):
        t = fi / 47
        img = gradient((w, h), colors).convert("RGBA")
        draw = ImageDraw.Draw(img)
        pulse = int(42 * math.sin(t * math.pi))
        draw.ellipse((70 - pulse, 115 - pulse, 315 + pulse, 360 + pulse), fill=(255, 255, 255, 36))
        draw.rounded_rectangle((42, 420, 342, 548), radius=26, fill=(0, 0, 0, 132))
        draw.text((66, 446), title, font=font(31, True), fill="#ffffff")
        draw.text((68, 495), "видео история", font=font(18), fill="#dbeafe")
        draw.rounded_rectangle((42, 38, 342, 44), radius=4, fill=(255, 255, 255, 60))
        draw.rounded_rectangle((42, 38, 42 + int(300 * t), 44), radius=4, fill=(255, 255, 255, 230))
        frames.append(np.asarray(img.convert("RGB")))
    imageio.mimsave(path, frames, fps=12, codec="libx264", quality=7, macro_block_size=16)


# ── media creation entry point ───────────────────────────────────────────────

def create_seed_media() -> None:
    if MEDIA_ROOT.exists():
        shutil.rmtree(MEDIA_ROOT)

    print("Generating avatars (Telegram-style gradient + initials)...")
    avatars = {
        "aziz":      ("Aziz Saidov",       ("#1d8ad6", "#0c2d52")),
        "laylo":     ("Laylo Rahimova",    ("#7c3aed", "#2e1065")),
        "bakhtiyor": ("Bakhtiyor Pulotov", ("#f97316", "#7c2d12")),
        "hamida":    ("Hamida Safarova",   ("#ec4899", "#831843")),
        "shahrukh":  ("Shahrukh Nazarov",  ("#0f766e", "#042f2e")),
        "nilufar":   ("Nilufar Yusupova",  ("#f59e0b", "#78350f")),
        "anush":     ("Anush Karimov",     ("#16a34a", "#14532d")),
        "malika":    ("Malika Karimova",   ("#2563eb", "#172554")),
        "farhod":    ("Farhod Rahmon",     ("#0891b2", "#164e63")),
        "zebo":      ("Zebo Nazarova",     ("#be123c", "#4c0519")),
        "nozim":     ("Nozim Dustov",      ("#64748b", "#1f2937")),
    }
    for key, (name, colors) in avatars.items():
        save_avatar(MEDIA_ROOT / "avatars" / f"{key}.jpg", name, colors)

    print("Downloading chat photos (picsum.photos)...")
    chat_photos = [
        ("code_review.jpg",     "office42",  "Code Review",       "FastAPI · WebSocket · auth flow",    ("#0f172a", "#1d4ed8")),
        ("softclub_class.jpg",  "study88",   "SoftClub",          "May group · 18:00–20:00",            ("#111827", "#059669")),
        ("dushanbe_evening.jpg","city55",    "Dushanbe evening",  "after class walk",                   ("#312e81", "#f97316")),
        ("design_notes.jpg",    "workspace71","Design notes",      "buttons · states · spacing",         ("#831843", "#0f172a")),
        ("mountains.jpg",       "nature33",  "Varzob road",       "weekend trip",                       ("#164e63", "#86efac")),
        ("release_board.jpg",   "office19",  "Release board",     "tasks before demo",                  ("#1e293b", "#7c3aed")),
    ]
    for fname, seed, title, subtitle, colors in chat_photos:
        save_photo(MEDIA_ROOT / "chats" / fname, seed, title, subtitle, colors)

    print("Downloading group photos...")
    group_media = [
        ("fastapi_group.jpg",  "code77",  "FastAPI May",   "7 участников · live practice",    ("#064e3b", "#0ea5e9")),
        ("django_group.jpg",   "code22",  "Django March",  "models · admin · serializers",    ("#14532d", "#1e293b")),
        ("github_group.jpg",   "tech44",  "Git/GitHub",    "branches · pull requests · deploy",("#111827", "#475569")),
    ]
    for fname, seed, title, subtitle, colors in group_media:
        save_photo(MEDIA_ROOT / "groups" / fname, seed, title, subtitle, colors)

    print("Downloading channel photos...")
    channel_media = [
        ("softclub.jpg",      "lecture55", "SoftClub Academy", "расписание и объявления",    ("#1e1b4b", "#7c3aed")),
        ("techpulse.jpg",     "tech99",    "Tech Pulse TJ",    "local dev news",             ("#0f172a", "#0369a1")),
        ("private_notes.jpg", "desk88",    "Private Notes",    "черновики и фиксы",          ("#022c22", "#0f766e")),
    ]
    for fname, seed, title, subtitle, colors in channel_media:
        save_photo(MEDIA_ROOT / "channels" / fname, seed, title, subtitle, colors)

    print("Downloading story photos (portrait)...")
    story_specs = [
        ("aziz_morning.jpg",      "morning11", "Душанбе, субҳ",    "пеш аз дарс",           ("#0f172a", "#38bdf8")),
        ("laylo_code.jpg",        "laptop44",  "React polish",     "buttons finally behave", ("#2e1065", "#a855f7")),
        ("bakhtiyor_city.jpg",    "street22",  "После кодинга",    "камтар ҳаво гирифтем",  ("#111827", "#f97316")),
        ("hamida_design.jpg",     "design33",  "UI notes",         "spacing зур шуд",        ("#831843", "#f472b6")),
        ("farhod_api.jpg",        "tech55",    "API check",        "swagger ҳамааш ok",      ("#164e63", "#22d3ee")),
        ("zebo_qa.jpg",           "office77",  "QA list",          "stories · auth · search",("#4c0519", "#fb7185")),
        ("malika_walk.jpg",       "city88",    "Шом ба хайр",      "city lights",            ("#312e81", "#f59e0b")),
    ]
    for fname, seed, title, subtitle, colors in story_specs:
        save_story_photo(MEDIA_ROOT / "stories" / fname, seed, title, subtitle, colors)

    print("Generating story videos...")
    save_story_video(MEDIA_ROOT / "stories" / "aziz_clip.mp4",   "Demo night",   ("#0f172a", "#2563eb"))
    save_story_video(MEDIA_ROOT / "stories" / "laylo_clip.mp4",  "Micro motion", ("#2e1065", "#ec4899"))
    save_story_video(MEDIA_ROOT / "stories" / "farhod_clip.mp4", "API pulse",    ("#083344", "#06b6d4"))

    print("All media ready.")


# ── database helpers ──────────────────────────────────────────────────────────

def create_user(db, key: str, phone_number: str, username: str, full_name: str, bio: str, is_online: bool, minutes_ago: int):
    now = get_dushanbe_time()
    user = User(
        phone_number=phone_number,
        created_at=now - timedelta(days=18, minutes=minutes_ago),
    )
    db.add(user)
    db.flush()

    profile = Profile(
        user_id=user.id,
        username=username,
        full_name=full_name,
        bio=bio,
        avatar_url=media_url(MEDIA_ROOT / "avatars" / f"{key}.jpg"),
        is_online=is_online,
        last_seen=None if is_online else now - timedelta(minutes=minutes_ago),
        created_at=now - timedelta(days=18, minutes=minutes_ago),
    )
    db.add(profile)
    db.flush()
    user.profile = profile
    return user


def create_users(db):
    users_data = [
        ("aziz",      "+992900000001", "azizsaidov",   "Aziz Saidov",       "Backend student. FastAPI, React and too many TODOs.",         True,  2),
        ("laylo",     "+992900000002", "laylo_dev",    "Laylo Rahimova",    "Frontend, motion and clean Telegram-like UI.",                False, 18),
        ("bakhtiyor", "+992900000003", "bakhtiyorpy",  "Bakhtiyor Pulotov", "Python mentor, code reviews after 18:00.",                    True,  5),
        ("hamida",    "+992900000004", "hamida_ui",    "Hamida Safarova",   "Design systems, spacing, dark themes.",                       False, 46),
        ("shahrukh",  "+992900000005", "shahrukhsql",  "Shahrukh Nazarov",  "SQL, Docker and small production rituals.",                   False, 75),
        ("nilufar",   "+992900000006", "nilufarux",    "Nilufar Yusupova",  "QA notes, screenshots and patient bug reports.",              True,  9),
        ("anush",     "+992900000007", "anushmobile",  "Anush Karimov",     "Mobile testing from an old Android phone.",                   False, 130),
        ("malika",    "+992900000008", "malikaqa",     "Malika Karimova",   "Frontend tester. I break buttons kindly.",                    True,  4),
        ("farhod",    "+992900000009", "farhodapi",    "Farhod Rahmon",     "FastAPI, SQLAlchemy, WebSocket.",                             False, 31),
        ("zebo",      "+992900000010", "zebo_pm",      "Zebo Nazarova",     "Product notes and release checklists.",                       False, 205),
        ("nozim",     "+992900000011", "nozim_old",    "Nozim Dustov",      "Old spam test account.",                                      False, 900),
    ]
    return {
        key: create_user(db, key, phone, username, full_name, bio, online, minutes_ago)
        for key, phone, username, full_name, bio, online, minutes_ago in users_data
    }


def create_contacts_and_blocks(db, users):
    contacts = [
        ("aziz", "laylo",     "Laylo frontend"),
        ("aziz", "bakhtiyor", "Bakhtiyor mentor"),
        ("aziz", "hamida",    "Hamida UI"),
        ("aziz", "shahrukh",  "Shahrukh SQL"),
        ("aziz", "nilufar",   "Nilufar QA"),
        ("aziz", "malika",    "Malika"),
        ("aziz", "farhod",    "Farhod API"),
        ("laylo",    "aziz",   "Aziz"),
        ("bakhtiyor","aziz",   "Aziz student"),
        ("hamida",   "laylo",  "Laylo"),
        ("malika",   "nilufar","Nilufar QA"),
    ]
    for owner, contact, name in contacts:
        db.add(Contact(owner_id=users[owner].id, contact_id=users[contact].id, name=name))

    db.add(BlockedUser(blocker_id=users["aziz"].id, blocked_id=users["nozim"].id))


# ── private chats ─────────────────────────────────────────────────────────────

def private_chat(db, users, first_key: str, second_key: str, rows: list[dict], created_days_ago: int = 8):
    now = get_dushanbe_time()
    first, second = users[first_key], users[second_key]
    chat = Chat(
        user_id_1=min(first.id, second.id),
        user_id_2=max(first.id, second.id),
        created_at=now - timedelta(days=created_days_ago),
    )
    db.add(chat)
    db.flush()

    messages = []
    for index, row in enumerate(rows):
        sender = users[row["from"]]
        media_name = row.get("media")
        reply_index = row.get("reply_to")
        forwarded_index = row.get("forwarded_from")
        message = Message(
            chat_id=chat.id,
            sender_id=sender.id,
            text=row.get("text"),
            media_url=media_url(MEDIA_ROOT / "chats" / media_name) if media_name else None,
            reply_to_id=messages[reply_index].id if reply_index is not None else None,
            forwarded_from_id=messages[forwarded_index].id if forwarded_index is not None else None,
            is_edited=row.get("edited", False),
            is_read=not (sender.id != users[CURRENT_USER].id and row.get("unread_for_aziz", False)),
            is_pinned=row.get("pinned", False),
            created_at=now - timedelta(minutes=row.get("minutes_ago", 120 - index * 7)),
        )
        db.add(message)
        db.flush()
        messages.append(message)

    for message_index, user_key, emoji in rows[0].get("reactions", []):
        db.add(MessageReaction(
            message_id=messages[message_index].id,
            user_id=users[user_key].id,
            emoji=emoji,
            created_at=messages[message_index].created_at + timedelta(minutes=1),
        ))

    return chat, messages


def create_private_chats(db, users):
    chats = {}

    chats["laylo"] = private_chat(db, users, "aziz", "laylo", [
        {"from": "laylo",  "text": "Салом, auth page-ро дидам. Акнун вход ва регистрация ҷудо шудааст?", "minutes_ago": 92},
        {"from": "aziz",   "text": "Ҳа, random number дигар account намесозад.", "minutes_ago": 88},
        {"from": "laylo",  "text": "Зӯр. Ман search by phone-ро ҳам дар modal месанҷам.", "minutes_ago": 84},
        {"from": "aziz",   "text": "Агар username набошад ҳам chat аз user_id кушода мешавад.", "minutes_ago": 80, "pinned": True},
        {"from": "laylo",  "text": "Ин screenshot барои UI spacing.", "minutes_ago": 42, "media": "design_notes.jpg"},
        {"from": "laylo",  "text": "Баъд story ring-ҳоро мебинам.", "minutes_ago": 21, "unread_for_aziz": True},
        {"from": "laylo",  "text": "Агар вақт шуд, фонро ҳам оромтар кун.", "minutes_ago": 14, "unread_for_aziz": True,
         "reactions": [(3, "laylo", "👍"), (4, "aziz", "🔥")]},
    ])

    chats["bakhtiyor"] = private_chat(db, users, "aziz", "bakhtiyor", [
        {"from": "bakhtiyor", "text": "Кодекс", "minutes_ago": 360},
        {"from": "aziz",      "text": "Устод, backend auth-ро ду endpoint кардам.", "minutes_ago": 350},
        {"from": "bakhtiyor", "text": "Login набояд user create кунад. Инро дуруст кардӣ?", "minutes_ago": 342},
        {"from": "aziz",      "text": "Ҳа. Register verify user/profile месозад.", "minutes_ago": 338},
        {"from": "bakhtiyor", "text": "Бисёр хуб. Seed-ро реалистичный кун.", "minutes_ago": 31, "unread_for_aziz": True},
    ])

    chats["hamida"] = private_chat(db, users, "aziz", "hamida", [
        {"from": "hamida", "text": "Ман дар stories ду круг барои як user медидам.", "minutes_ago": 250},
        {"from": "aziz",   "text": "Ҳозир myGroup-ро алоҳида merge кардам.", "minutes_ago": 248},
        {"from": "hamida", "text": "Ин фон ба Telegram наздиктар аст?", "minutes_ago": 240, "media": "dushanbe_evening.jpg"},
        {"from": "aziz",   "text": "Ҳа, лекин дар polish step боз беҳтар мекунем.", "minutes_ago": 236, "reply_to": 2},
        {"from": "hamida", "text": "Ок, ман баъд mobile-ро мебинам.", "minutes_ago": 26, "unread_for_aziz": True},
    ])

    chats["shahrukh"] = private_chat(db, users, "aziz", "shahrukh", [
        {"from": "aziz",     "text": "SQLite reset мешавад, чизе нигоҳ дорем?", "minutes_ago": 520},
        {"from": "shahrukh", "text": "Не, учебный проект аст. Drop and recreate.", "minutes_ago": 512},
        {"from": "shahrukh", "text": "Фақат migrations надорем, create_all кофӣ.", "minutes_ago": 506},
        {"from": "aziz",     "text": "Медиа низ дар media/seed меравад.", "minutes_ago": 500},
        {"from": "shahrukh", "text": "Пас database.db тоза мешавад.", "minutes_ago": 190},
    ])

    chats["nilufar"] = private_chat(db, users, "aziz", "nilufar", [
        {"from": "nilufar", "text": "Bug list: auth, stories, search, buttons.", "minutes_ago": 610},
        {"from": "aziz",    "text": "Auth ва stories done. Seeds ҳозир.", "minutes_ago": 600},
        {"from": "nilufar", "text": "Ин тасвирро ҳамчун media message гузор.", "minutes_ago": 594, "media": "release_board.jpg"},
        {"from": "nilufar", "text": "Нишонаҳои unread ҳам лозим.", "minutes_ago": 18, "unread_for_aziz": True},
    ])

    chats["malika"] = private_chat(db, users, "aziz", "malika", [
        {"from": "malika", "text": "Build гузашт?", "minutes_ago": 88},
        {"from": "aziz",   "text": "Ҳа, Vite build ok.", "minutes_ago": 84},
        {"from": "malika", "text": "Browser console?", "minutes_ago": 80},
        {"from": "aziz",   "text": "No errors.", "minutes_ago": 76},
        {"from": "malika", "text": "Баъди seed боз як маротиба login санҷ.", "minutes_ago": 11, "unread_for_aziz": True},
    ])

    chats["anush"] = private_chat(db, users, "aziz", "anush", [
        {"from": "anush", "text": "Дар телефони ман sidebar танг мешавад.", "minutes_ago": 800},
        {"from": "aziz",  "text": "Responsive баъди seeds polish мекунем.", "minutes_ago": 792},
        {"from": "anush", "text": "Ман video story ҳам мехоҳам.", "minutes_ago": 785},
        {"from": "aziz",  "text": "MP4 seed илова мешавад.", "minutes_ago": 778},
    ])

    return chats


# ── groups ────────────────────────────────────────────────────────────────────

def create_group_with_messages(db, users, name: str, avatar_file: str, description: str,
                                member_roles: list[tuple[str, str]], rows: list[dict], read_before: int):
    now = get_dushanbe_time()
    group = Group(
        owner_id=users[member_roles[0][0]].id,
        name=name,
        avatar_url=media_url(MEDIA_ROOT / "groups" / avatar_file),
        description=description,
        created_at=now - timedelta(days=6),
    )
    db.add(group)
    db.flush()

    for username, role in member_roles:
        db.add(GroupMember(
            group_id=group.id,
            user_id=users[username].id,
            role=role,
            joined_at=now - timedelta(days=6),
        ))
    db.flush()

    messages = []
    for index, row in enumerate(rows):
        media_name = row.get("media")
        message = GroupMessage(
            group_id=group.id,
            sender_id=users[row["from"]].id,
            text=row.get("text"),
            media_url=media_url(MEDIA_ROOT / "groups" / media_name) if media_name else None,
            reply_to_id=messages[row["reply_to"]].id if row.get("reply_to") is not None else None,
            forwarded_from_id=messages[row["forwarded_from"]].id if row.get("forwarded_from") is not None else None,
            is_edited=row.get("edited", False),
            is_pinned=row.get("pinned", False),
            created_at=now - timedelta(minutes=row.get("minutes_ago", 260 - index * 12)),
        )
        db.add(message)
        db.flush()
        messages.append(message)

    for index, message in enumerate(messages[2::4]):
        user_key = member_roles[(index + 2) % len(member_roles)][0]
        db.add(GroupMessageReaction(
            message_id=message.id,
            user_id=users[user_key].id,
            emoji=["👍", "🔥", "👏", "❤️"][index % 4],
            created_at=message.created_at + timedelta(minutes=2),
        ))

    if read_before and len(messages) > read_before:
        db.add(GroupReadState(
            group_id=group.id,
            user_id=users[CURRENT_USER].id,
            last_read_message_id=messages[-read_before].id,
            updated_at=now - timedelta(minutes=15),
        ))

    return group, messages


def create_groups(db, users):
    fastapi_rows = [
        {"from": "bakhtiyor", "text": "Ассалому алайкум, гурӯҳи FastAPI May. Имрӯз auth ва WebSocket-ро мебинем.", "minutes_ago": 310, "pinned": True},
        {"from": "aziz",      "text": "Ман login/register-ро ҷудо кардам.", "minutes_ago": 300},
        {"from": "farhod",    "text": "Swagger screenshot:", "minutes_ago": 294, "media": "fastapi_group.jpg"},
        {"from": "laylo",     "text": "Frontend ҳам endpoints навро истифода мебарад.", "minutes_ago": 282},
        {"from": "hamida",    "text": "Story ring after view бояд gray шавад.", "minutes_ago": 270},
        {"from": "zebo",      "text": "QA: random phone дар login набояд user созад.", "minutes_ago": 246},
        {"from": "bakhtiyor", "text": "Ҳама инро пеш аз seeds test кунед.", "minutes_ago": 230, "reply_to": 5},
        {"from": "malika",    "text": "Search by phone ok, username ҳам кор мекунад.", "minutes_ago": 112},
        {"from": "nilufar",   "text": "Ман mobile viewport-ро баъд аз UI polish мебинам.", "minutes_ago": 58},
        {"from": "farhod",    "text": "Seed data бояд realistic бошад, post # не.", "minutes_ago": 37},
        {"from": "laylo",     "text": "Ҳозир аллакай беҳтар менамояд.", "minutes_ago": 19},
    ]
    django_rows = [
        {"from": "shahrukh", "text": "Django group archive: касе migration questions дорад?", "minutes_ago": 900, "pinned": True},
        {"from": "aziz",     "text": "Дар FastAPI create_all истифода шуд, migrations нест.", "minutes_ago": 870},
        {"from": "shahrukh", "text": "Барои учебный project ok.", "minutes_ago": 860},
        {"from": "anush",    "text": "Ман media upload-ро бо телефон месанҷам.", "minutes_ago": 830},
        {"from": "hamida",   "text": "Ин design notes аз моҳи март:", "minutes_ago": 810, "media": "django_group.jpg"},
    ]
    github_rows = [
        {"from": "farhod",  "text": "Git/GitHub: branch-ҳоро пеш аз commit тоза нигоҳ доред.", "minutes_ago": 760, "pinned": True},
        {"from": "aziz",    "text": "Ман ҳоло commit намекунам, step by step меравам.", "minutes_ago": 750},
        {"from": "zebo",    "text": "Ҳар step баъди build report шавад.", "minutes_ago": 742},
        {"from": "malika",  "text": "Ин schema дар PR description лозим мешавад.", "minutes_ago": 720, "media": "github_group.jpg"},
    ]

    return {
        "fastapi": create_group_with_messages(
            db, users,
            "FastAPI May 18:00-20:00", "fastapi_group.jpg",
            "Гурӯҳи омӯзишӣ барои FastAPI, SQLAlchemy ва realtime.",
            [("bakhtiyor", "admin"), ("aziz", "admin"), ("laylo", "member"), ("hamida", "member"),
             ("farhod", "member"), ("zebo", "member"), ("malika", "member"), ("nilufar", "member")],
            fastapi_rows, read_before=4,
        ),
        "django": create_group_with_messages(
            db, users,
            "Django 1 March 16:00-18:00", "django_group.jpg",
            "Archive group for Django lessons and old homework.",
            [("shahrukh", "admin"), ("aziz", "member"), ("anush", "member"), ("hamida", "member")],
            django_rows, read_before=2,
        ),
        "github": create_group_with_messages(
            db, users,
            "Git/GitHub December 16-18", "github_group.jpg",
            "Branches, pull requests and deploy notes.",
            [("farhod", "admin"), ("aziz", "member"), ("zebo", "member"), ("malika", "member")],
            github_rows, read_before=0,
        ),
    }


# ── channels ──────────────────────────────────────────────────────────────────

def create_channel(db, users, name: str, avatar_file: str, description: str, owner: str,
                   members: list[tuple[str, str]], posts: list[dict], read_before: int):
    now = get_dushanbe_time()
    channel = Channel(
        owner_id=users[owner].id,
        name=name,
        avatar_url=media_url(MEDIA_ROOT / "channels" / avatar_file),
        description=description,
        is_public=not name.startswith("Private"),
        created_at=now - timedelta(days=5),
    )
    db.add(channel)
    db.flush()

    for username, role in members:
        db.add(ChannelMember(channel_id=channel.id, user_id=users[username].id, role=role, joined_at=now - timedelta(days=5)))
    db.flush()

    channel_posts = []
    for index, row in enumerate(posts):
        media_name = row.get("media")
        post = ChannelPost(
            channel_id=channel.id,
            sender_id=users[row["from"]].id,
            text=row["text"],
            media_url=media_url(MEDIA_ROOT / "channels" / media_name) if media_name else None,
            is_edited=row.get("edited", False),
            is_pinned=row.get("pinned", False),
            created_at=now - timedelta(minutes=row.get("minutes_ago", 500 - index * 40)),
        )
        db.add(post)
        db.flush()
        channel_posts.append(post)

    for index, post in enumerate(channel_posts):
        for username in ["aziz", "laylo", "hamida", "malika", "zebo"]:
            if username in users and users[username].id != post.sender_id and (index + users[username].id) % 2 == 0:
                db.add(ChannelPostReaction(
                    post_id=post.id,
                    user_id=users[username].id,
                    emoji=["👍", "🔥", "❤️", "👀"][index % 4],
                    created_at=post.created_at + timedelta(minutes=3),
                ))

    if read_before and len(channel_posts) > read_before:
        db.add(ChannelReadState(
            channel_id=channel.id,
            user_id=users[CURRENT_USER].id,
            last_read_post_id=channel_posts[-read_before].id,
            updated_at=now - timedelta(minutes=20),
        ))

    return channel, channel_posts


def create_channels(db, users):
    softclub_posts = [
        {"from": "bakhtiyor", "text": "📌 Таквими моҳи май: FastAPI аз 18:00 то 20:00, чор рӯз дар ҳафта.", "media": "softclub.jpg", "minutes_ago": 980, "pinned": True},
        {"from": "bakhtiyor", "text": "Имрӯз дарс: auth flow, OTP, profile ва seed data.", "minutes_ago": 760},
        {"from": "farhod",    "text": "Poll: кадом қисми clone-ро аввал polish кунем?", "minutes_ago": 620},
        {"from": "bakhtiyor", "text": "Reminder: ҳар кас project-и худро бо realistic data нишон медиҳад.", "minutes_ago": 240},
    ]
    tech_posts = [
        {"from": "farhod", "text": "FastAPI tip: response_model-ро барои frontend state фаромӯш накунед.", "media": "techpulse.jpg", "minutes_ago": 840, "pinned": True},
        {"from": "farhod", "text": "SQLAlchemy: unread counters-ро бо read_state нигоҳ доштан қулай аст.", "minutes_ago": 600},
        {"from": "laylo",  "text": "Frontend note: empty buttons are bugs, not future features.", "minutes_ago": 410},
        {"from": "farhod", "text": "Stories: server should send has_unviewed, client should not guess.", "minutes_ago": 95},
    ]
    private_posts = [
        {"from": "aziz", "text": "Private note: after auth split, old verify endpoint is login alias.", "media": "private_notes.jpg", "minutes_ago": 520, "pinned": True},
        {"from": "aziz", "text": "Need to check CORS after localhost/frontend restart.", "minutes_ago": 310},
        {"from": "aziz", "text": "Seed reset is allowed for this учебный project.", "minutes_ago": 80},
    ]

    channels = {
        "softclub": create_channel(
            db, users, "SoftClub Academy", "softclub.jpg",
            "Расписание, объявления и полезные материалы для студентов.", "bakhtiyor",
            [("bakhtiyor", "admin"), ("aziz", "subscriber"), ("laylo", "subscriber"),
             ("hamida", "subscriber"), ("farhod", "subscriber"), ("zebo", "subscriber"), ("malika", "subscriber")],
            softclub_posts, read_before=2,
        ),
        "tech": create_channel(
            db, users, "Tech Pulse TJ", "techpulse.jpg",
            "Локальные заметки про backend, frontend и продуктовую разработку.", "farhod",
            [("farhod", "admin"), ("laylo", "admin"), ("aziz", "subscriber"),
             ("malika", "subscriber"), ("zebo", "subscriber"), ("nilufar", "subscriber")],
            tech_posts, read_before=1,
        ),
        "private": create_channel(
            db, users, "Private Backend Notes", "private_notes.jpg",
            "Закрытый канал с черновиками решений и проверками.", "aziz",
            [("aziz", "admin"), ("laylo", "subscriber"), ("malika", "subscriber")],
            private_posts, read_before=0,
        ),
    }

    poll = Poll(channel_post_id=channels["softclub"][1][2].id, question="Что полировать следующим?")
    db.add(poll)
    db.flush()

    options = []
    for text in ["Stories viewer", "Mobile sidebar", "Message composer", "Settings page"]:
        opt = PollOption(poll_id=poll.id, text=text)
        db.add(opt)
        db.flush()
        options.append(opt)

    for username, option in [("aziz", options[0]), ("laylo", options[2]), ("hamida", options[0]),
                              ("malika", options[1]), ("zebo", options[3])]:
        db.add(PollVote(poll_id=poll.id, option_id=option.id, user_id=users[username].id))

    return channels


# ── stories ───────────────────────────────────────────────────────────────────

def create_stories(db, users):
    now = get_dushanbe_time()
    story_rows = [
        ("aziz",      "aziz_morning.jpg",     "photo", 130),
        ("aziz",      "aziz_clip.mp4",        "video",  95),
        ("laylo",     "laylo_code.jpg",        "photo",  70),
        ("laylo",     "laylo_clip.mp4",        "video",  34),
        ("bakhtiyor", "bakhtiyor_city.jpg",    "photo", 210),
        ("hamida",    "hamida_design.jpg",     "photo", 150),
        ("farhod",    "farhod_api.jpg",        "photo",  90),
        ("farhod",    "farhod_clip.mp4",       "video",  44),
        ("zebo",      "zebo_qa.jpg",           "photo",  62),
        ("malika",    "malika_walk.jpg",       "photo",  24),
    ]
    stories = []
    for owner, file_name, media_type, minutes_ago in story_rows:
        story = Story(
            user_id=users[owner].id,
            media_url=media_url(MEDIA_ROOT / "stories" / file_name),
            media_type=media_type,
            expires_at=now + timedelta(hours=22, minutes=minutes_ago % 40),
            created_at=now - timedelta(minutes=minutes_ago),
        )
        db.add(story)
        db.flush()
        stories.append((owner, story))

    viewed_by_aziz = {"bakhtiyor", "hamida"}
    for owner, story in stories:
        viewers = ["laylo", "hamida", "malika", "farhod", "zebo"]
        if owner in viewed_by_aziz:
            viewers.append("aziz")
        for viewer in viewers:
            if viewer != owner and users[viewer].id != story.user_id and (story.id + users[viewer].id) % 2 == 0:
                db.add(StoryView(story_id=story.id, user_id=users[viewer].id, created_at=story.created_at + timedelta(minutes=12)))

    return [story for _, story in stories]


# ── notifications ─────────────────────────────────────────────────────────────

def create_notifications(db, users, private_chats, groups, channels):
    now = get_dushanbe_time()
    rows = [
        ("aziz", "laylo",     "message",      private_chats["laylo"][1][-1].id,      "message",      False, 18),
        ("aziz", "bakhtiyor", "group_message", groups["fastapi"][1][-1].id,           "group_message", False, 15),
        ("aziz", "farhod",    "channel_post",  channels["tech"][1][-1].id,            "channel_post",  False, 11),
        ("aziz", "bakhtiyor", "channel_post",  channels["softclub"][1][-1].id,        "channel_post",  True,  95),
        ("laylo","aziz",      "reaction",      private_chats["laylo"][1][3].id,        "message",       False, 32),
    ]
    for to_user, from_user, type_, entity_id, entity_type, is_read, minutes_ago in rows:
        db.add(Notification(
            to_user_id=users[to_user].id,
            from_user_id=users[from_user].id,
            type=type_,
            entity_id=entity_id,
            entity_type=entity_type,
            is_read=is_read,
            created_at=now - timedelta(minutes=minutes_ago),
        ))


# ── entry point ───────────────────────────────────────────────────────────────

def seed_database():
    create_seed_media()

    print("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("Seeding users...")
        users = create_users(db)
        create_contacts_and_blocks(db, users)

        print("Seeding chats...")
        private_chats = create_private_chats(db, users)

        print("Seeding groups...")
        groups = create_groups(db, users)

        print("Seeding channels...")
        channels = create_channels(db, users)

        print("Seeding stories...")
        create_stories(db, users)

        print("Seeding notifications...")
        create_notifications(db, users, private_chats, groups, channels)

        db.query(OTPCode).delete()
        db.commit()
    finally:
        db.close()

    print("\nSeed complete.")
    print("Login: +992900000001  (Aziz Saidov)")
    print("Others: +992900000002 … +992900000011")
    print("Use /users/login/request-otp — the response contains the dev OTP code.")


if __name__ == "__main__":
    seed_database()

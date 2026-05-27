from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from utils import get_dushanbe_time


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_dushanbe_time, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("ChannelMember", back_populates="channel", cascade="all, delete-orphan")
    posts = relationship("ChannelPost", back_populates="channel", cascade="all, delete-orphan")


class ChannelMember(Base):
    __tablename__ = "channel_members"
    __table_args__ = (
        UniqueConstraint("channel_id", "user_id", name="uq_channel_user_member"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="subscriber", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_dushanbe_time, nullable=False)

    channel = relationship("Channel", back_populates="members")
    user = relationship("User")


class ChannelPost(Base):
    __tablename__ = "channel_posts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_dushanbe_time, nullable=False)

    channel = relationship("Channel", back_populates="posts")
    sender = relationship("User", foreign_keys=[sender_id])
    reactions = relationship("ChannelPostReaction", back_populates="post", cascade="all, delete-orphan")


class ChannelPostReaction(Base):
    __tablename__ = "channel_post_reactions"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_channel_post_user_reaction"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("channel_posts.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    emoji: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_dushanbe_time, nullable=False)

    post = relationship("ChannelPost", back_populates="reactions")
    user = relationship("User")


class ChannelReadState(Base):
    __tablename__ = "channel_read_states"
    __table_args__ = (
        UniqueConstraint("channel_id", "user_id", name="uq_channel_user_read_state"),
        CheckConstraint("last_read_post_id IS NULL OR last_read_post_id > 0", name="ck_channel_last_read_post_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    last_read_post_id: Mapped[int | None] = mapped_column(ForeignKey("channel_posts.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_dushanbe_time, onupdate=get_dushanbe_time, nullable=False)

    channel = relationship("Channel")
    user = relationship("User")
    last_read_post = relationship("ChannelPost")

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from utils import get_dushanbe_time


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_dushanbe_time, nullable=False)

    owner = relationship("User", foreign_keys=[owner_id])
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    messages = relationship("GroupMessage", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user_member"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="member", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_dushanbe_time, nullable=False)

    group = relationship("Group", back_populates="members")
    user = relationship("User")


class GroupMessage(Base):
    __tablename__ = "group_messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    media_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reply_to_id: Mapped[int | None] = mapped_column(ForeignKey("group_messages.id", ondelete="SET NULL"), nullable=True)
    forwarded_from_id: Mapped[int | None] = mapped_column(ForeignKey("group_messages.id", ondelete="SET NULL"), nullable=True)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_dushanbe_time, nullable=False)

    group = relationship("Group", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])
    reply_to = relationship("GroupMessage", remote_side=[id], foreign_keys=[reply_to_id])
    forwarded_from = relationship("GroupMessage", remote_side=[id], foreign_keys=[forwarded_from_id])
    reactions = relationship("GroupMessageReaction", back_populates="message", cascade="all, delete-orphan")


class GroupMessageReaction(Base):
    __tablename__ = "group_message_reactions"
    __table_args__ = (
        UniqueConstraint("message_id", "user_id", name="uq_group_message_user_reaction"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    message_id: Mapped[int] = mapped_column(ForeignKey("group_messages.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    emoji: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_dushanbe_time, nullable=False)

    message = relationship("GroupMessage", back_populates="reactions")
    user = relationship("User")


class GroupReadState(Base):
    __tablename__ = "group_read_states"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_user_read_state"),
        CheckConstraint("last_read_message_id IS NULL OR last_read_message_id > 0", name="ck_group_last_read_message_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    last_read_message_id: Mapped[int | None] = mapped_column(ForeignKey("group_messages.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_dushanbe_time, onupdate=get_dushanbe_time, nullable=False)

    group = relationship("Group")
    user = relationship("User")
    last_read_message = relationship("GroupMessage")

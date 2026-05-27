from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from utils import get_dushanbe_time


class BlockedUser(Base):
    __tablename__ = "blocked_users"
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_blocker_blocked"),
        CheckConstraint("blocker_id != blocked_id", name="ck_blocked_user_not_self"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    blocker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    blocked_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_dushanbe_time, nullable=False)

    blocker = relationship("User", foreign_keys=[blocker_id])
    blocked = relationship("User", foreign_keys=[blocked_id])

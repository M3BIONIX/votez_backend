from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, Boolean, func, ForeignKey
from sqlalchemy.orm import Mapped, relationship, mapped_column
from core.base import VersionedMixin, Base

class Poll(VersionedMixin, Base):
    __tablename__ = "poll"

    title: Mapped[str] = mapped_column(String(50), nullable=False)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    poll_options: Mapped[List["PollOptions"]] = relationship(back_populates="poll", cascade="all, delete-orphan")
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now() ,nullable=False)


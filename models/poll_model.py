from datetime import datetime
from typing import List
from sqlalchemy import String, Integer, DateTime, Boolean, func, event
from sqlalchemy.orm import Mapped, relationship, mapped_column
from core.base import VersionedMixin, Base, update_version_id_on_change


class Poll(VersionedMixin, Base):
    __tablename__ = "poll"

    title: Mapped[str] = mapped_column(String(50), nullable=False)
    poll_options: Mapped[List["PollOptions"]] = relationship(back_populates="poll", cascade="all, delete-orphan")
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now() ,nullable=False)

event.listens_for(Poll.poll_options, "append")(update_version_id_on_change)
event.listens_for(Poll.poll_options, "remove")(update_version_id_on_change)

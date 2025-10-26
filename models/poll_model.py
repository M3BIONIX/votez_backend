from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.testing.schema import mapped_column

from core.base import VersionedMixin, Base
from models.poll_options_model import PollOptions


class Poll(VersionedMixin, Base):
    __tablename__ = "poll"

    title: Mapped[str] = mapped_column(String(50), nullable=False)
    poll_options: Mapped[PollOptions] = relationship(PollOptions, foreign_keys=[PollOptions.id])
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now() ,nullable=False)



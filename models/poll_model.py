from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, func, event
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.testing.schema import mapped_column

from core.base import VersionedMixin, Base, update_version_id_on_change
from models.poll_options_model import PollOptions


class Poll(VersionedMixin, Base):
    __tablename__ = "poll"

    title: Mapped[str] = mapped_column(String(50), nullable=False)
    poll_options: Mapped[PollOptions] = relationship(PollOptions, foreign_keys=[PollOptions.id])
    likes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now() ,nullable=False)

event.listens_for(Poll.poll_options, "append")(update_version_id_on_change)
event.listens_for(Poll.poll_options, "remove")(update_version_id_on_change)

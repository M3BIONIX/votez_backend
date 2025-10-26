from datetime import datetime

from sqlalchemy import Integer, ForeignKey, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from core.base import VersionedMixin, Base


class PollOptions(VersionedMixin, Base):
    __tablename__ = 'poll_options'

    poll_id: Mapped[int] = mapped_column(Integer, ForeignKey("poll.id"), nullable=False)
    option_name: Mapped[str] = mapped_column(String(50), nullable=False)
    votes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)



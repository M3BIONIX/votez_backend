from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base


class Vote(Base):
    __tablename__ = "votes"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    poll_id: Mapped[int] = mapped_column(Integer, ForeignKey("poll.id"), nullable=False)
    option_id: Mapped[int] = mapped_column(Integer, ForeignKey("poll_options.id"), nullable=False)


from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from core.base import Base


class UserModel(Base):
    __tablename__ = "users"

    name: Mapped[String] = mapped_column(String(50), nullable=False)
    email: Mapped[String] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

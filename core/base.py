from sqlalchemy import Integer, Sequence, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr


class VersionedMixin:
    version_id: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    @declared_attr
    def __mapper_args__(self):
        return {"version_id_col": self.version_id}

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(Integer, Sequence("id_seq", start=1000), primary_key=True)
    uuid: Mapped[UUID] = mapped_column(UUID(as_uuid=True), server_default=text("gen_random_uuid()"), nullable=False)

    @declared_attr
    def __tablename__(self) -> str:
        return self.__name__.lower()

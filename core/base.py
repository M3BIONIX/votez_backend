from sqlalchemy import Column, Integer, Sequence, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr, object_session


class VersionedMixin:
    @declared_attr
    def version_id(self) -> Column[int]:
        return Column("version_id", Integer, nullable=False, server_default=text("1"), autoincrement=False)

    # Specify the version_id column for optimistic concurrency control
    @declared_attr
    def __mapper_args__(self):
        if hasattr(self, "version_id"):
            return {"version_id_col": self.version_id}
        return {}

class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(Integer, Sequence("id_seq", start=1000), primary_key=True)
    uuid: Mapped[UUID] = mapped_column(UUID, server_default=text("uuid_generate_v4()"), nullable=False)

    @declared_attr
    def __tablename__(self) -> str:
        return self.__name__.lower()

def update_version_id_on_change(target):
    if object_session(target) is not None:
        target.version_id += 1
        object_session(target).add(target)


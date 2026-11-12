from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.model_mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from src.modules.auth.infrastructure.models import Account


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)

    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    account: Mapped["Account | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.model_mixins import UUIDPrimaryKeyMixin, TimestampMixin
from src.modules.auth.domain.enums import AccountStatus


if TYPE_CHECKING:
    from src.modules.users.infrastructure.models import User

class Account(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete = "CASCADE"),
        unique = True,
        nullable = False
    )

    username: Mapped[str] = mapped_column(
        String(30),
        unique = True,
        nullable = False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique = True,
        nullable = False
    )

    password_hash: Mapped[str] = mapped_column(
        String(250),
        nullable = False
    )

    status: Mapped[AccountStatus] = mapped_column(
        Enum(
            AccountStatus,
            name = "account_status",
            values_callable = lambda enum_type:[
                status.value for status in enum_type
            ]
        ),
        default = AccountStatus.ACTIVE,
        nullable = False
    )

    user: Mapped["User"] = relationship(
        back_populates = "account"
    )


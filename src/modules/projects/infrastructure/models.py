from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.model_mixins import TimestampMixin, UUIDPrimaryKeyMixin
from src.modules.projects.domain.enums import ProjectRole, ProjectStatus


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"

    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable = False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable = False
    )

    description: Mapped[str] = mapped_column(
        String(5000),
        nullable = True
    )

    status: Mapped[ProjectStatus] = mapped_column(
        Enum(
            ProjectStatus,
            name = "project_status",
            values_callable = lambda status_types:[
                status.value for status in status_types
            ]
        ),
        default = ProjectStatus.ACTIVE,
        server_default = ProjectStatus.ACTIVE.value,
        nullable=False
    )

    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

Index(
    "uq_projects_owner_id_lower_name",
    Project.owner_id,
    func.lower(Project.name),
    unique=True
)

class ProjectMember(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "project_members"

    __table_args__ = (
        UniqueConstraint(
            "project_id", "user_id",
            name = "uq_project_members_project_id_user_id"
        ),
        Index(
            "uq_project_member_one_active_owner",
            "project_id",
            unique=True,
            postgresql_where = text("role = 'owner' AND left_at IS NULL")
        ),
        Index(
            "ix_project_members_user_id_active",
            "user_id",
            postgresql_where = text("left_at IS NULL")
        )
    )

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    role: Mapped[ProjectRole] = mapped_column(
        Enum(
            ProjectRole,
            name = "project_role",
            values_callable = lambda role_types:[
                role.value for role in role_types
            ]
        ),
        nullable = False
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    left_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

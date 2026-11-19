from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.model_mixins import TimestampMixin, UUIDPrimaryKeyMixin
from src.modules.tasks.domain.enums import TaskPriority, TaskStatus


class Task(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tasks"

    __table_args__ = (
        Index("ix_tasks_project_id_status", "project_id", "status"),
        Index("ix_tasks_project_id_assigned_to", "project_id", "assigned_to"),
    )

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)

    description: Mapped[str | None] = mapped_column(String(5000), nullable=True)

    status: Mapped[TaskStatus] = mapped_column(
        Enum(
            TaskStatus,
            name="task_status",
            values_callable=lambda status_types: [status.value for status in status_types],
        ),
        default=TaskStatus.PENDING,
        server_default=TaskStatus.PENDING.value,
        nullable=False,
    )

    priority: Mapped[TaskPriority] = mapped_column(
        Enum(
            TaskPriority,
            name="task_priority",
            values_callable=lambda priority_types: [priority.value for priority in priority_types],
        ),
        default=TaskPriority.LOW,
        server_default=TaskPriority.LOW.value,
        nullable=False,
    )

    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    assigned_to: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)

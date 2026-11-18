from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.modules.tasks.domain.enums import TaskPriority, TaskStatus


@dataclass
class Task:
    id: UUID
    project_id: UUID
    title: str
    created_by: UUID
    description: str | None = None
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.LOW
    assigned_to: UUID | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class TaskDetail:
    task: Task
    created_by_username: str
    assigned_to_username: str | None = None
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, StringConstraints

from src.core.pagination import PaginationParams
from src.modules.tasks.domain.enums import TaskPriority, TaskStatus

TITLE_MAX = 200
DESCRIPTION_MAX = 5000

TaskTitleStr = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TITLE_MAX)
]
TaskDescriptionStr = Annotated[str, StringConstraints(max_length=DESCRIPTION_MAX)]
UsernameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=3)]
SearchStr = Annotated[str, StringConstraints(strip_whitespace=True, max_length=TITLE_MAX)]


class CreateTaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: TaskTitleStr
    description: TaskDescriptionStr | None = None
    priority: TaskPriority = TaskPriority.LOW
    assigned_to: UsernameStr | None = None


class TaskResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    created_by: str
    assigned_to: str | None
    created_at: datetime
    updated_at: datetime


class TaskListParams(PaginationParams):
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    assigned_to: UsernameStr | None = None
    search: SearchStr | None = None

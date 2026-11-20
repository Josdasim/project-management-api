from typing import Protocol
from uuid import UUID

from src.modules.tasks.domain.entities import Task
from src.modules.tasks.domain.enums import TaskPriority, TaskStatus


class TaskRepository(Protocol):
    def add(self, task: Task) -> Task: ...
    def get_by_id_and_project(self, task_id: UUID, project_id: UUID) -> Task | None: ...
    def list_by_project(
        self,
        project_id: UUID,
        *,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        assigned_to: UUID | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> list[Task]: ...
    def count_by_project(
        self,
        project_id: UUID,
        *,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        assigned_to: UUID | None,
        search: str | None,
    ) -> int: ...
    def update(self, task: Task) -> Task: ...
    def delete(self, task: Task) -> None: ...

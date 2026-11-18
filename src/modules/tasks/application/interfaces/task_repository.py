from typing import Protocol

from src.modules.tasks.domain.entities import Task


class TaskRepository(Protocol):
    def add(self, task: Task) -> Task: ...
from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.projects.public import ProjectNotFoundError, ProjectRepository, ProjectRole
from src.modules.tasks.application.interfaces.task_repository import TaskRepository
from src.modules.tasks.domain.exceptions import TaskNotFoundError, TaskPermissionDeniedError


class DeleteTaskService:
    def __init__(
        self, task: TaskRepository, project: ProjectRepository, unit_work: UnitOfWork
    ) -> None:
        self._task = task
        self._project = project
        self._unit_work = unit_work

    def delete(self, *, project_id: UUID, task_id: UUID, actor_id: UUID) -> None:
        actor = self._project.get_by_id_and_member(project_id, actor_id)

        if actor is None:
            raise ProjectNotFoundError

        task = self._task.get_by_id_and_project(task_id, project_id)
        if task is None:
            raise TaskNotFoundError

        if actor.role not in (ProjectRole.OWNER, ProjectRole.ADMIN):
            raise TaskPermissionDeniedError

        self._task.delete(task)
        self._unit_work.commit()

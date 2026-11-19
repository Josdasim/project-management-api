from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.auth.public import AccountRepository
from src.modules.projects.public import ProjectNotFoundError, ProjectRepository, ProjectRole
from src.modules.tasks.application.interfaces.task_repository import TaskRepository
from src.modules.tasks.application.task_details import to_details
from src.modules.tasks.domain.entities import TaskDetail
from src.modules.tasks.domain.enums import TaskStatus
from src.modules.tasks.domain.exceptions import (
    InvalidStatusTransitionError,
    TaskNotFoundError,
    TaskPermissionDeniedError,
)
from src.modules.tasks.domain.transitions import ALLOWED_TRANSITIONS


class ChangeTaskStatusService:
    def __init__(
        self,
        task: TaskRepository,
        project: ProjectRepository,
        account: AccountRepository,
        unit_work: UnitOfWork,
    ) -> None:
        self._task = task
        self._project = project
        self._account = account
        self._unit_work = unit_work

    def change_status(
        self, *, project_id: UUID, task_id: UUID, actor_id: UUID, status: TaskStatus
    ) -> TaskDetail:
        actor = self._project.get_by_id_and_member(project_id, actor_id)
        if actor is None:
            raise ProjectNotFoundError

        task = self._task.get_by_id_and_project(task_id, project_id)
        if task is None:
            raise TaskNotFoundError

        is_manager = actor.role in (ProjectRole.OWNER, ProjectRole.ADMIN)
        is_assignee = actor.role == ProjectRole.MEMBER and task.assigned_to == actor_id
        if not (is_manager or is_assignee):
            raise TaskPermissionDeniedError

        if status not in ALLOWED_TRANSITIONS[task.status]:
            raise InvalidStatusTransitionError

        task.status = status
        updated = self._task.update(task)
        self._unit_work.commit()

        return to_details(self._account, [updated])[0]

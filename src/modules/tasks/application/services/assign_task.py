from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.auth.public import AccountRepository
from src.modules.projects.public import (
    ProjectMemberRepository,
    ProjectNotFoundError,
    ProjectRepository,
    ProjectRole,
)
from src.modules.tasks.application.assignee import validate_assignee
from src.modules.tasks.application.interfaces.task_repository import TaskRepository
from src.modules.tasks.application.task_details import to_details
from src.modules.tasks.domain.entities import TaskDetail
from src.modules.tasks.domain.enums import TaskStatus
from src.modules.tasks.domain.exceptions import (
    TaskNotEditableError,
    TaskNotFoundError,
    TaskPermissionDeniedError,
)


class AssignTaskService:
    def __init__(
        self,
        task: TaskRepository,
        project: ProjectRepository,
        member: ProjectMemberRepository,
        account: AccountRepository,
        unit_work: UnitOfWork,
    ) -> None:
        self._task = task
        self._project = project
        self._member = member
        self._account = account
        self._unit_work = unit_work

    def assign(
        self, *, project_id: UUID, task_id: UUID, actor_id: UUID, assigned_to: str | None
    ) -> TaskDetail:
        actor = self._project.get_by_id_and_member(project_id, actor_id)
        if actor is None:
            raise ProjectNotFoundError

        task = self._task.get_by_id_and_project(task_id, project_id)
        if task is None:
            raise TaskNotFoundError

        if actor.role == ProjectRole.VIEWER:
            raise TaskPermissionDeniedError

        account = None if assigned_to is None else self._account.get_by_username(assigned_to)

        if actor.role == ProjectRole.MEMBER:
            if assigned_to is None:
                allowed = task.assigned_to == actor_id
            else:
                is_self = account is not None and account.user_id == actor_id
                allowed = is_self and task.assigned_to in (None, actor_id)
            if not allowed:
                raise TaskPermissionDeniedError

        if task.status in (TaskStatus.COMPLETED, TaskStatus.CANCELLED):
            raise TaskNotEditableError

        task.assigned_to = (
            None if assigned_to is None else validate_assignee(self._member, project_id, account)
        )
        updated = self._task.update(task)
        self._unit_work.commit()

        return to_details(self._account, [updated])[0]

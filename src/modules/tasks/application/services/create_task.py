import uuid
from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.auth.public import AccountRepository, AccountStatus
from src.modules.projects.public import (
    ProjectMemberRepository,
    ProjectNotFoundError,
    ProjectRepository,
    ProjectRole,
)
from src.modules.tasks.application.interfaces.task_repository import TaskRepository
from src.modules.tasks.domain.entities import Task, TaskDetail
from src.modules.tasks.domain.enums import TaskPriority
from src.modules.tasks.domain.exceptions import InvalidAssigneeError, TaskPermissionDeniedError


class CreateTaskService:
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

    def create(
        self,
        *,
        project_id: UUID,
        actor_id: UUID,
        title: str,
        description: str | None = None,
        priority: TaskPriority = TaskPriority.LOW,
        assigned_to: str | None = None,
    ) -> TaskDetail:
        actor = self._project.get_by_id_and_member(project_id, actor_id)
        if actor is None:
            raise ProjectNotFoundError
        if actor.role == ProjectRole.VIEWER:
            raise TaskPermissionDeniedError

        assignee_id = None
        if assigned_to is not None:
            account = self._account.get_by_username(assigned_to)
            if actor.role == ProjectRole.MEMBER and (
                account is None or account.user_id != actor_id
            ):
                raise TaskPermissionDeniedError
            if account is None or account.status != AccountStatus.ACTIVE:
                raise InvalidAssigneeError
            membership = self._member.get_by_project_and_user(project_id, account.user_id)
            if (
                membership is None
                or membership.left_at is not None
                or membership.role == ProjectRole.VIEWER
            ):
                raise InvalidAssigneeError
            assignee_id = account.user_id

        task = self._task.add(
            Task(
                id=uuid.uuid7(),
                project_id=project_id,
                title=title.strip(),
                description=description,
                priority=priority,
                created_by=actor_id,
                assigned_to=assignee_id,
            )
        )
        self._unit_work.commit()

        user_ids = [actor_id] if assignee_id is None else [actor_id, assignee_id]
        usernames = {a.user_id: a.username for a in self._account.list_by_user_ids(user_ids)}
        return TaskDetail(
            task=task,
            created_by_username=usernames[actor_id],
            assigned_to_username=usernames[assignee_id] if assignee_id else None,
        )

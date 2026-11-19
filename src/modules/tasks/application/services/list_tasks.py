from uuid import UUID

from src.core.pagination import Page
from src.modules.auth.public import AccountRepository
from src.modules.projects.public import ProjectNotFoundError, ProjectRepository
from src.modules.tasks.application.interfaces.task_repository import TaskRepository
from src.modules.tasks.application.task_details import to_details
from src.modules.tasks.domain.entities import TaskDetail
from src.modules.tasks.domain.enums import TaskPriority, TaskStatus


class ListTasksService:
    def __init__(
        self, task: TaskRepository, project: ProjectRepository, account: AccountRepository
    ) -> None:
        self._task = task
        self._project = project
        self._account = account

    def list_tasks(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        status: TaskStatus | None,
        priority: TaskPriority | None,
        assigned_to: str | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> Page[TaskDetail]:
        if self._project.get_by_id_and_member(project_id, user_id) is None:
            raise ProjectNotFoundError

        assignee_id = None
        if assigned_to is not None:
            account = self._account.get_by_username(assigned_to)
            if account is None:
                return Page(items=[], total=0, page=page, page_size=page_size)
            assignee_id = account.user_id

        filters = {
            "status": status,
            "priority": priority,
            "assigned_to": assignee_id,
            "search": search,
        }
        offset = (page - 1) * page_size
        tasks = self._task.list_by_project(project_id, **filters, limit=page_size, offset=offset)
        total = self._task.count_by_project(project_id, **filters)

        return Page(
            items=to_details(self._account, tasks), total=total, page=page, page_size=page_size
        )

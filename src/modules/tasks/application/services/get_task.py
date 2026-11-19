from uuid import UUID

from src.modules.auth.public import AccountRepository
from src.modules.projects.public import ProjectNotFoundError, ProjectRepository
from src.modules.tasks.application.interfaces.task_repository import TaskRepository
from src.modules.tasks.application.task_details import to_details
from src.modules.tasks.domain.entities import TaskDetail
from src.modules.tasks.domain.exceptions import TaskNotFoundError


class GetTaskService:
    def __init__(
        self, task: TaskRepository, project: ProjectRepository, account: AccountRepository
    ) -> None:
        self._task = task
        self._project = project
        self._account = account

    def get(self, *, project_id: UUID, task_id: UUID, user_id: UUID) -> TaskDetail:
        if self._project.get_by_id_and_member(project_id, user_id) is None:
            raise ProjectNotFoundError

        task = self._task.get_by_id_and_project(task_id, project_id)
        if task is None:
            raise TaskNotFoundError

        return to_details(self._account, [task])[0]

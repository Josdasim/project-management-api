from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.entities import ProjectWithRole
from src.modules.projects.domain.exceptions import ProjectNotDeletedError, ProjectNotFoundError


class RestoreProjectService:
    def __init__(self, project: ProjectRepository, unit_work: UnitOfWork) -> None:
        self._project = project
        self._unit_work = unit_work

    def restore(self, *, project_id: UUID, user_id: UUID) -> ProjectWithRole:
        project = self._project.get_by_id_and_owner(project_id, user_id)
        if project is None:
            raise ProjectNotFoundError
        if project.deleted_at is None:
            raise ProjectNotDeletedError

        project.deleted_at = None
        self._project.update(project)
        self._unit_work.commit()

        return self._project.get_by_id_and_member(project_id, user_id)

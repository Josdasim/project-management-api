from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.exceptions import ProjectNotFoundError, ProjectNotDeletedError


class DeleteProjectPermanentlyService:
    def __init__(self, project: ProjectRepository, unit_work: UnitOfWork) -> None:
        self._project = project
        self._unit_work = unit_work

    def delete_permanently(self, *, project_id: UUID, user_id: UUID) -> None:
        self._project.lock(project_id)

        project = self._project.get_by_id_and_member(project_id, user_id)

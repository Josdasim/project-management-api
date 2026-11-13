from uuid import UUID

from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.entities import ProjectWithRole
from src.modules.projects.domain.exceptions import ProjectNotFoundError


class GetProjectService:
    def __init__(self, project: ProjectRepository) -> None:
        self._project = project

    def get(self, *, project_id: UUID, user_id: UUID) -> ProjectWithRole:
        found = self._project.get_by_id_and_member(project_id, user_id)

        if found is None:
            raise ProjectNotFoundError

        return found

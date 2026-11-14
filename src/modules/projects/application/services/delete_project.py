from datetime import UTC, datetime
from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.domain.exceptions import (
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
)


class DeleteProjectService:
    def __init__(self, project: ProjectRepository, unit_work: UnitOfWork) -> None:
        self._project = project
        self._unit_work = unit_work

    def delete(self, *, project_id: UUID, user_id: UUID) -> None:
        found = self._project.get_by_id_and_member(project_id, user_id)

        if found is None:
            raise ProjectNotFoundError

        if found.role != ProjectRole.OWNER:
            raise ProjectPermissionDeniedError

        project = found.project
        project.deleted_at = datetime.now(UTC)
        self._project.update(project)
        self._unit_work.commit()

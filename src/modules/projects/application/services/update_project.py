from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.entities import ProjectWithRole
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.domain.exceptions import (
    ProjectNameAlreadyExistsError,
    ProjectNotFoundError,
    ProjectPermissionDeniedError,
)


class UpdateProjectService:
    def __init__(self, project: ProjectRepository, unit_wort: UnitOfWork) -> None:
        self._project = project
        self._unit_work = unit_wort

    def update(
        self, *, project_id: UUID, user_id: UUID, changes: dict[str, str | None]
    ) -> ProjectWithRole:
        found = self._project.get_by_id_and_member(project_id, user_id)

        if found is None:
            raise ProjectNotFoundError
        if found.role not in (ProjectRole.OWNER, ProjectRole.ADMIN):
            raise ProjectPermissionDeniedError
        if "name" in changes and found.role != ProjectRole.OWNER:
            raise ProjectPermissionDeniedError

        project = found.project

        if "name" in changes:
            name = changes["name"]

            if self._project.name_exists(project.owner_id, name, exclude_project_id=project.id):
                raise ProjectNameAlreadyExistsError
            project.name = name

        if "description" in changes:
            project.description = changes["description"]
        updated = self._project.update(project)
        self._unit_work.commit()

        return ProjectWithRole(project=updated, role=found.role)

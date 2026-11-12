import uuid
from datetime import datetime, UTC
from uuid import UUID

from src.core.unit_of_work import UnitOfWork
from src.modules.projects.application.interfaces.projec_member_repository import(
    ProjectMemberRepository
)
from src.modules.projects.application.interfaces.project_repository import ProjectRepository
from src.modules.projects.domain.entities import Project, ProjectMember
from src.modules.projects.domain.enums import ProjectRole
from src.modules.projects.domain.exceptions import ProjectNameAlreadyExistsError


class CreateProjectService:
    def __init__(
            self,
            project:ProjectRepository,
            member: ProjectMemberRepository,
            unit_work: UnitOfWork
    ) -> None:
        self._project = project
        self._member = member
        self._unit_work = unit_work

    def create(
            self, *,
            owner_id: UUID,
            name: str,
            description: str | None = None
    ) -> Project:
        name = name.strip()

        if self._project.name_exists(owner_id, name):
            raise ProjectNameAlreadyExistsError

        project = self._project.add(
            Project(
                id=uuid.uuid7(),
                owner_id=owner_id,
                name=name,
                description=description
            )
        )
        self._member.add(
            ProjectMember(
                id=uuid.uuid7(),
                project_id=project.id,
                user_id=owner_id,
                role=ProjectRole.OWNER,
                joined_at=datetime.now(UTC)
            )
        )
        self._unit_work.commit()
        return project
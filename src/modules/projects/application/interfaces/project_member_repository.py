from typing import Protocol
from uuid import UUID

from src.modules.projects.domain.entities import ProjectMember
from src.modules.projects.domain.enums import ProjectRole


class ProjectMemberRepository(Protocol):
    def add(self, member: ProjectMember) -> ProjectMember: ...
    def get_by_project_and_user(self, project_id: UUID, user_id: UUID) -> ProjectMember: ...
    def update(self, member: ProjectMember) -> ProjectMember: ...
    def list_active_by_project(
        self, project_id: UUID, *, role: ProjectRole | None = None
    ) -> list[ProjectMember]: ...

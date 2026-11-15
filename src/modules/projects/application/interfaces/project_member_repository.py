from typing import Protocol
from uuid import UUID

from src.modules.projects.domain.entities import ProjectMember


class ProjectMemberRepository(Protocol):
    def add(self, member: ProjectMember) -> ProjectMember: ...
    def get_by_project_and_user(self, project_id: UUID, user_id: UUID) -> ProjectMember: ...
    def update(self, member: ProjectMember) -> ProjectMember: ...

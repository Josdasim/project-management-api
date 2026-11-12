from typing import Protocol

from src.modules.projects.domain.entities import ProjectMember


class ProjectMemberRepository(Protocol):
    def add(self, memeber: ProjectMember) -> ProjectMember: ...

from typing import Protocol
from uuid import UUID

from src.modules.projects.domain.entities import Project


class ProjectRepository(Protocol):
    def name_exists(self, owner_id: UUID, name: str) -> bool: ...
    def add(self, project: Project) -> Project: ...

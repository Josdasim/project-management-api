from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from src.modules.projects.domain.enums import ProjectRole, ProjectStatus


@dataclass
class Project:
    id: UUID
    owner_id: UUID
    name: str
    description: str | None = None
    status: ProjectStatus = ProjectStatus.ACTIVE
    deleted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class ProjectMember:
    id: UUID
    project_id: UUID
    user_id: UUID
    role: ProjectRole
    joined_at: datetime
    left_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass
class ProjectWithRole:
    project: Project
    role: ProjectRole
